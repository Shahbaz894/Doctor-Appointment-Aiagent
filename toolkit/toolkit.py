import pandas as pd
from typing import Literal
from langchain_core.tools import tool
from data_models.models import *
from logger.logging import logger
from datetime import datetime


@tool
def check_availability_by_doctor(desired_date: DateModel, doctor_name: Literal[
    'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller',
    'sarah wilson', 'michael green', 'lisa brown', 'jane smith', 'emily johnson', 'john doe'
]):
    """Checking availability by doctor"""
    logger.info(f"Checking availability for Dr. {doctor_name} on {desired_date.date}")
    try:
        df = pd.read_csv('data/doctor_availability.csv')
        logger.debug("CSV loaded successfully")

        df['date_slot_time'] = df['date_slot'].apply(lambda x: x.split(' ')[-1])
        rows = list(df[(df['date_slot'].apply(lambda x: x.split(' ')[0]) == desired_date.date) &
                       (df['doctor_name'] == doctor_name) & 
                       (df['is_available'] == True)]['date_slot_time'])

        if not rows:
            logger.info("No availability found")
            return 'No availability in the entire day'
        else:
            logger.info(f"Available slots found: {rows}")
            return f"This availability for {desired_date.date}\nAvailable slots: {', '.join(rows)}"
    except Exception as e:
        logger.error(f"Error in check_availability_by_doctor: {e}")
        return "An error occurred while checking availability."


@tool
def check_availability_by_specialization(desired_date: DateModel, specialization: Literal[
    "general_dentist", "cosmetic_dentist", "prosthodontist", "pediatric_dentist",
    "emergency_dentist", "oral_surgeon", "orthodontist"
]):
    """Checking availability by specialization"""
    logger.info(f"Checking availability for specialization: {specialization} on {desired_date.date}")
    try:
        df = pd.read_csv('data/doctor_availability.csv')
        df['date_slot_time'] = df['date_slot'].apply(lambda x: x.split(' ')[-1])

        rows = df[(df['date_slot'].apply(lambda x: x.split(' ')[0]) == desired_date.date) &
                  (df['specialization'] == specialization) & 
                  (df['is_available'] == True)] \
                .groupby(['specialization', 'doctor_name'])['date_slot_time'] \
                .apply(list).reset_index(name='available_slots')

        if rows.empty:
            logger.info("No availability found")
            return "No availability in the entire day"
        else:
            logger.info("Available slots found")

            def convert_to_am_pm(time_str):
                hours, minutes = map(int, str(time_str).split(":"))
                period = "AM" if hours < 12 else "PM"
                hours = hours % 12 or 12
                return f"{hours}:{minutes:02d} {period}"

            output = f"This availability for {desired_date.date}\n"
            for row in rows.values:
                output += f"{row[1]}. Available slots: \n" + ', \n'.join([convert_to_am_pm(t) for t in row[2]]) + '\n'
            return output
    except Exception as e:
        logger.error(f"Error in check_availability_by_specialization: {e}")
        return "An error occurred while checking availability."


@tool
def set_appointment(desired_date: DateTimeModel, id_number: IdentificationNumberModel, doctor_name: Literal[
    'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller',
    'sarah wilson', 'michael green', 'lisa brown', 'jane smith', 'emily johnson', 'john doe'
]):
    """Set an appointment with a doctor"""
    logger.info(f"Setting appointment for {doctor_name} on {desired_date.date} for ID: {id_number.id}")
    try:
        df = pd.read_csv('E:/Doctor-Appointment-Aiagent/data/doctor.csv')

        def convert_datetime_format(dt_str):
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
            return dt.strftime("%d-%m-%Y %#H.%M")

        formatted_date = convert_datetime_format(desired_date.date)

        case = df[(df['date_slot'] == formatted_date) &
                  (df['doctor_name'] == doctor_name) &
                  (df['is_available'] == True)]

        if case.empty:
            logger.warning("No available appointment slot found")
            return "No available appointments for that particular case"
        else:
            df.loc[(df['date_slot'] == formatted_date) &
                   (df['doctor_name'] == doctor_name), ['is_available', 'patient_to_attend']] = [False, id_number.id]

            df.to_csv('availability.csv', index=False)
            logger.info("Appointment set successfully")
            return "Successfully done"
    except Exception as e:
        logger.error(f"Error in set_appointment: {e}")
        return "An error occurred while setting the appointment."


@tool
def cancel_appointment(date: DateTimeModel, id_number: IdentificationNumberModel, doctor_name: Literal[
    'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller',
    'sarah wilson', 'michael green', 'lisa brown', 'jane smith', 'emily johnson', 'john doe'
]):
    """Cancel an existing appointment"""
    logger.info(f"Attempting to cancel appointment for {doctor_name} on {date.date} with ID: {id_number.id}")
    try:
        df = pd.read_csv('E:/Doctor-Appointment-Aiagent/data/doctor.csv')

        case_to_remove = df[(df['date_slot'] == date.date) &
                            (df['patient_to_attend'] == id_number.id) &
                            (df['doctor_name'] == doctor_name)]

        if case_to_remove.empty:
            logger.warning("No appointment found with specified parameters")
            return "You don’t have any appointment with that specification"
        else:
            df.loc[(df['date_slot'] == date.date) &
                   (df['patient_to_attend'] == id_number.id) &
                   (df['doctor_name'] == doctor_name), ['is_available', 'patient_to_attend']] = [True, None]

            df.to_csv('availability.csv', index=False)
            logger.info("Appointment cancelled successfully")
            return "Successfully cancelled"
    except Exception as e:
        logger.error(f"Error in cancel_appointment: {e}")
        return "An error occurred while cancelling the appointment."


@tool
def reschedule_appointment(old_date: DateTimeModel, new_date: DateTimeModel, id_number: IdentificationNumberModel, doctor_name: Literal[
    'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller',
    'sarah wilson', 'michael green', 'lisa brown', 'jane smith', 'emily johnson', 'john doe'
]):
    """Reschedule an existing appointment"""
    logger.info(f"Rescheduling appointment for {doctor_name} from {old_date.date} to {new_date.date} for ID: {id_number.id}")
    try:
        df = pd.read_csv("E:/Doctor-Appointment-Aiagent/data/doctor.csv")
        available = df[(df['date_slot'] == new_date.date) &
                       (df['is_available'] == True) &
                       (df['doctor_name'] == doctor_name)]

        if available.empty:
            logger.warning("No available slots on the new date")
            return "Not available slots in the desired period"
        else:
            cancel_appointment.invoke({
                'date': old_date,
                'id_number': id_number,
                'doctor_name': doctor_name
            })

            set_appointment.invoke({
                'desired_date': new_date,
                'id_number': id_number,
                'doctor_name': doctor_name
            })

            logger.info("Appointment rescheduled successfully")
            return "Successfully rescheduled for the desired time"
    except Exception as e:
        logger.error(f"Error in reschedule_appointment: {e}")
        return "An error occurred while rescheduling the appointment."
