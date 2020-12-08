import pandas as pd
import numpy

from src.classes.data_from_server_user import DataFromServerAboutUsers
from src.classes.user import User
from src.classes.address import Address
from src.classes.doc import Doc
from src.classes.employee import Employee
from src.classes.passport import Passport
from src.data_validate import gender_validate, date_validate, phone_validate, authority_code_validate, \
    postal_code_validate, snils_validate, email_validate, region_code_validate, number_validate, serial_number_validate, \
    inn_validate, not_null_name_validate, hr_manager_validate, head_manager_validate, external_id_validate, \
    passport_exists, email_exists, phone_exists, snils_exists, inn_exists


# получение значения, прошедшего валидацию, из ячейки СНИЛС
def get_snils(row):
    return snils_validate(row['СНИЛС'])


# если паспорт, СНИЛС, или ИНН не существуют на сервере, и
# если email, phone не существуют на сервере, и
# если значения из ячеек серия паспорта, номер паспорта, СНИЛС, ИНН, фамилия, имя непустые и прошли валидацию,
# то данные одной строки проходят валидацию и записываюстся в объект класса User и в объект класса Employee
def data2class(row, data_users):
    passport_number = number_validate(row['Паспорт:Номер'])
    passport_serial_number = serial_number_validate(row['Паспорт:Серия'])

    snils = snils_validate(row['СНИЛС'])
    inn = inn_validate(row['ИНН ФЛ'])
    if passport_exists(passport_serial_number + passport_number, data_users) or snils_exists(snils,
                                                                                             data_users) or inn_exists(
        inn, data_users):
        return False, False

    first_name = not_null_name_validate(row['Имя'])
    last_name = not_null_name_validate(row['Фамилия'])

    head_manager = head_manager_validate(row['Руководитель'])
    hr_manager = hr_manager_validate(row['Кадровый сотрудник'])

    phone = phone_validate(row['Номер телефона'])
    email = email_validate(row['Электронная почта'])

    if email_exists(email, data_users) or phone_exists(phone, data_users):
        return False, False

    if (passport_number and passport_serial_number and snils and inn) and (first_name and last_name) and (
            head_manager is not None) and (hr_manager is not None):
        user = User(last_name, first_name)
        user.patronymic = row['Отчество']

        user.gender = gender_validate(row['Пол'])
        user.birthdate = date_validate(row['Дата рождения'])
        user.phone = phone
        user.email = email

        user.personalDocuments = []
        passport = Passport('PASSPORT', passport_number, passport_serial_number)
        passport.issuedDate = date_validate(row['Паспорт:Дата выдачи'])
        passport.issuingAuthority = row['Паспорт:Кем выдан']
        passport.issuingAuthorityCode = authority_code_validate(row['Паспорт:Код подразделения'])
        passport.birthplace = row['Паспорт:Место рождения']

        address = Address()
        address.postalCode = postal_code_validate(row['Адрес регистрации:Почтовый индекс'])
        address.regionCode = region_code_validate(row['Адрес регистрации:Регион'])
        address.city = row['Адрес регистрации:Город']
        address.street = row['Адрес регистрации:Улица']
        address.house = row['Адрес регистрации:Дом']
        address.block = row['Адрес регистрации:Корпус/строение']
        address.flat = row['Адрес регистрации:Квартира']

        passport.registrationAddress = address
        user.personalDocuments.append(passport)
        user.personalDocuments.append(Doc('SNILS', snils))
        user.personalDocuments.append(Doc('INN', inn))

        employee = Employee(row['Юрлицо'], head_manager, hr_manager)
        employee.department = row['Отдел']
        employee.position = row['Должность']
        employee.externalId = external_id_validate(row['ID сотрудника во внешней системе'])

        data_users.lst_person_snils.append(snils)
        data_users.lst_person_inn.append(inn)
        data_users.lst_person_passport.append(passport_serial_number + passport_number)
        data_users.lst_person_email_phone.append(email)
        data_users.lst_person_email_phone.append(phone)
        data_users.lst_person_email_phone = list(filter(None, data_users.lst_person_email_phone))
        data_users.lst_person_email_phone = list(filter(None, data_users.lst_person_email_phone))
        return user, employee
    else:
        return False, False


# excel таблица переводится в df
# удаляются три ненужные верхние строки (название, да/нет, пример)
# удаляется ненужный первый столбец
# убираются все переводы строк, значения ячеек триммируюстя справа и слева
# все значения в ячейках приводятся к строковому типу
def xlsx2df(excel_name):
    try:
        df = pd.read_excel(excel_name, sheet_name=0)
        df.drop([0, 1, 2], inplace=True)
        df.drop(df.columns[0], axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.columns = df.columns.str.replace('\n', '')
        df.columns = df.columns.str.strip()

        df = df.astype(str)
        df.replace('nan', numpy.nan, inplace=True)
        return df
    except FileNotFoundError:
        return False
