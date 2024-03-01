from urllib.parse import urlencode
import aiohttp
from datetime import datetime, timezone
from . import Authenticator, Utils
import json
import pytz


class Client:
    _authenticator: Authenticator

    def __init__(self, authenticator: Authenticator):
        self._authenticator = authenticator

    async def get_profile(self, with_groups=False, with_parents=False, with_assignments=False,
                          with_ec_attendances=False, with_ae_attendances=False,
                          with_home_based_periods=False, with_lesson_comments=False, with_attendances=False,
                          with_final_marks=False,
                          with_marks=False, with_subjects=False, with_lesson_info=False):
        options = {
            "with_groups": with_groups,
            "with_parents": with_parents,
            "with_assignments": with_assignments,
            "with_ec_attendances": with_ec_attendances,
            "with_ae_attendances": with_ae_attendances,
            "with_home_based_periods": with_home_based_periods,
            "with_lesson_comments": with_lesson_comments,
            "with_attendances": with_attendances,
            "with_final_marks": with_final_marks,
            "with_marks": with_marks,
            "with_subjects": with_subjects,
            "with_lesson_info": with_lesson_info
        }

        query = ""
        for key in options:
            if options[key]:
                query += key + "=true&"

        async with aiohttp.ClientSession() as session:
            async with await session.get("https://dnevnik.mos.ru/core/api/student_profiles/" + str(
                    await self._authenticator.get_student_id()) + "?" + query[:-1], headers={
                "Auth-Token": await self._authenticator.get_token(),
                "Profile-Id": await self._authenticator.get_student_id()
            }) as response:
                res = await response.json()

                res["created_at"] = None if "created_at" not in res else datetime.strptime(res["created_at"],
                                                                                           "%d.%m.%Y %H:%M")
                res["updated_at"] = None if "updated_at" not in res else datetime.strptime(res["updated_at"],
                                                                                           "%d.%m.%Y %H:%M")
                res["deleted_at"] = None if "deleted_at" not in res else datetime.strptime(res["deleted_at"],
                                                                                           "%d.%m.%Y %H:%M")
                res["birth_date"] = None if "birth_date" not in res else datetime.strptime(res["birth_date"],
                                                                                           "%d.%m.%Y")

                res["left_on"] = None if "left_on" not in res else datetime.strptime(res["left_on"], "%d.%m.%Y")
                res["enlisted_on"] = None if "enlisted_on" not in res else datetime.strptime(res["enlisted_on"],
                                                                                             "%d.%m.%Y")
                res["migration_date"] = None if "migration_date" not in res else datetime.strptime(
                    res["migration_date"], "%d.%m.%Y")
                res["last_sign_in_at"] = None if "last_sign_in_at" not in res else datetime.strptime(
                    res["last_sign_in_at"], "%d.%m.%Y %H:%M")
                res["left_on_registry"] = None if "left_on_registry" not in res else datetime.strptime(
                    res["left_on_registry"], "%d.%m.%Y")

                for parent in res["parents"]:
                    parent["last_sign_in_at"] = None if "last_sign_in_at" not in parent else datetime.strptime(
                        parent["last_sign_in_at"], "%d.%m.%Y %H:%M")

                for group in res["groups"]:
                    group["begin_date"] = None if "begin_date" not in group else datetime.strptime(
                        group["begin_date"], "%d.%m.%Y")
                    group["end_date"] = None if "end_date" not in group else datetime.strptime(group["end_date"],
                                                                                               "%d.%m.%Y")

                for mark in res["marks"]:
                    mark["date"] = None if "date" not in mark else datetime.strptime(mark["date"], "%d.%m.%Y")
                    mark["point_date"] = None if "point_date" not in mark else datetime.strptime(mark["point_date"],
                                                                                                 "%d.%m.%Y")

                for final_mark in res["final_marks"]:
                    final_mark["created_at"] = None if "created_at" not in final_mark else datetime.strptime(
                        final_mark["created_at"], "%d.%m.%Y %H:%M")
                    final_mark["updated_at"] = None if "updated_at" not in final_mark else datetime.strptime(
                        final_mark["updated_at"], "%d.%m.%Y %H:%M")
                    final_mark["deleted_at"] = None if "deleted_at" not in final_mark else datetime.strptime(
                        final_mark["deleted_at"], "%d.%m.%Y %H:%M")

                return res

    async def get_average_marks(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dnevnik.mos.ru/reports/api/progress/json?academic_year_id=" + str(
                    (await self.get_current_academic_year())["id"]) + "&student_profile_id=" + str(
                await self._authenticator.get_student_id()), headers={
                "Auth-Token": await self._authenticator.get_token(),
                "Profile-Id": await self._authenticator.get_student_id()
            }) as response:
                result = []
                for lesson in await response.json():
                    if len(lesson["periods"]) != 0:
                        period = lesson["periods"][-1]
                        marks = []
                        for mark in period["marks"]:
                            marks.append({"mark": mark["values"][0]["five"], "weight": mark["weight"]})
                        result.append({"name": lesson["subject_name"],
                                       "mark": Utils.average(Utils.parse_marks_with_weight(marks))})
                return result

    async def get_subjects(self, lessons=None):
        if lessons is None:
            lessons = []
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dnevnik.mos.ru/core/api/subjects?ids=" + ",".join(lessons), headers={
                "Cookie": "auth_token=" + await self._authenticator.get_token() + "; student_id=" + str(
                    await self._authenticator.get_student_id()) + ";",
                "Auth-token": await self._authenticator.get_token(),
                "Profile-Id": await self._authenticator.get_student_id()
            }) as response:
                return await response.json()

    async def get_marks(self, from_date=datetime.now(), to_date=datetime.now()):
        url = f"https://dnevnik.mos.ru/core/api/marks?created_at_from={from_date.strftime('%d.%m.%Y')}&created_at_to={to_date.strftime('%d.%m.%Y')}&student_profile_id={await self._authenticator.get_student_id()}"
        headers = {
            "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
            "Auth-token": await self._authenticator.get_token(),
            "Profile-Id": await self._authenticator.get_student_id()
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()

        for d in data:
            d['created_at'] = datetime.strptime(d['created_at'], '%d.%m.%Y %H:%M')
            d['updated_at'] = datetime.strptime(d['updated_at'], '%d.%m.%Y %H:%M')
            d['date'] = datetime.strptime(d['date'], '%d.%m.%Y')

        return data

    async def get_homework(self, from_date=datetime.now(), to_date=datetime.now()):
        url = f"https://dnevnik.mos.ru/core/api/student_homeworks?begin_prepared_date={from_date.strftime('%d.%m.%Y')}&end_prepared_date={to_date.strftime('%d.%m.%Y')}&student_profile_id={await self._authenticator.get_student_id()}"
        headers = {
            "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
            "Auth-token": await self._authenticator.get_token(),
            "Profile-Id": await self._authenticator.get_student_id()
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()

        for d in data:
            d['created_at'] = datetime.strptime(d['created_at'], '%d.%m.%Y %H:%M') if d['created_at'] else None
            d['updated_at'] = datetime.strptime(d['updated_at'], '%d.%m.%Y %H:%M') if d['updated_at'] else None
            d['deleted_at'] = datetime.strptime(d['deleted_at'], '%d.%m.%Y %H:%M') if d['deleted_at'] else None

            d['homework_entry']['created_at'] = datetime.strptime(d['homework_entry']['created_at'],
                                                                  '%d.%m.%Y %H:%M') if d['homework_entry'][
                'created_at'] else None
            d['homework_entry']['updated_at'] = datetime.strptime(d['homework_entry']['updated_at'],
                                                                  '%d.%m.%Y %H:%M') if d['homework_entry'][
                'updated_at'] else None
            d['homework_entry']['deleted_at'] = datetime.strptime(d['homework_entry']['deleted_at'],
                                                                  '%d.%m.%Y %H:%M') if d['homework_entry'][
                'deleted_at'] else None

            d['homework_entry']['homework']['created_at'] = datetime.strptime(
                d['homework_entry']['homework']['created_at'], '%d.%m.%Y %H:%M') if d['homework_entry']['homework'][
                'created_at'] else None
            d['homework_entry']['homework']['updated_at'] = datetime.strptime(
                d['homework_entry']['homework']['updated_at'], '%d.%m.%Y %H:%M') if d['homework_entry']['homework'][
                'updated_at'] else None
            d['homework_entry']['homework']['deleted_at'] = datetime.strptime(
                d['homework_entry']['homework']['deleted_at'], '%d.%m.%Y %H:%M') if d['homework_entry']['homework'][
                'deleted_at'] else None
            d['homework_entry']['homework']['date_assigned_on'] = datetime.strptime(
                d['homework_entry']['homework']['date_assigned_on'], '%d.%m.%Y') if d['homework_entry']['homework'][
                'date_assigned_on'] else None
            d['homework_entry']['homework']['date_prepared_for'] = datetime.strptime(
                d['homework_entry']['homework']['date_prepared_for'], '%d.%m.%Y') if d['homework_entry']['homework'][
                'date_prepared_for'] else None

        return data

    async def get_events(self, from_date=datetime.now(), to_date=datetime.now(), expand=None,
                         person_id=None):
        if expand is None:
            expand = {}
        if person_id is None:
            profile = await self.get_profile()
            person_id = profile['person_id']

        ex = [key for key, value in expand.items() if value]

        params = {
            'person_ids': person_id,
            'begin_date': from_date.strftime('%Y-%m-%d'),
            'end_date': to_date.strftime('%Y-%m-%d'),
            'expand': ','.join(ex)
        }

        url = f"https://school.mos.ru/api/eventcalendar/v1/api/events?{urlencode(params)}"
        headers = {
            "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
            "Auth-Token": await self._authenticator.get_token(),
            "Profile-Id": await self._authenticator.get_student_id(),
            "authorization": f"Bearer {await self._authenticator.get_token()}",
            "x-mes-role": "student",
            "x-mes-subsystem": "familyweb"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()

        for event in data['response']:
            event['start_at'] = datetime.fromisoformat(event['start_at'])
            event['finish_at'] = datetime.fromisoformat(event['finish_at'])
            if event['created_at']:
                event['created_at'] = datetime.fromisoformat(event['created_at'])
            if event['updated_at']:
                event['updated_at'] = datetime.fromisoformat(event['updated_at'])
            if event['registration_start_at']:
                event['registration_start_at'] = datetime.fromisoformat(event['registration_start_at'])
            if event['registration_end_at']:
                event['registration_end_at'] = datetime.fromisoformat(event['registration_end_at'])

        return data

    async def get_teacher(self, id):
        url = f"https://dnevnik.mos.ru/core/api/teacher_profiles/{id}"
        headers = {
            "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
            "Auth-token": await self._authenticator.get_token(),
            "Profile-Id": await self._authenticator.get_student_id()
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()

        data['created_at'] = datetime.fromisoformat(data['created_at']) if data['created_at'] else None
        data['updated_at'] = datetime.fromisoformat(data['updated_at']) if data['updated_at'] else None
        data['deleted_at'] = datetime.fromisoformat(data['deleted_at']) if data['deleted_at'] else None

        for building in data['buildings']:
            building['created_at'] = datetime.fromisoformat(building['created_at']) if building[
                'created_at'] else None
            building['updated_at'] = datetime.fromisoformat(building['updated_at']) if building[
                'updated_at'] else None
            building['deleted_at'] = datetime.fromisoformat(building['deleted_at']) if building[
                'deleted_at'] else None

        for room in data['rooms']:
            room['created_at'] = datetime.fromisoformat(room['created_at']) if room['created_at'] else None
            room['updated_at'] = datetime.fromisoformat(room['updated_at']) if room['updated_at'] else None
            room['deleted_at'] = datetime.fromisoformat(room['deleted_at']) if room['deleted_at'] else None

        return data

    async def get_teams_links(self, date=datetime.now()):
        schedule = await self.get_schedule(date)

        links = []

        for lesson in schedule['response']:
            if lesson['type'] != 'LESSON':
                continue
            if lesson['lesson']['lesson_type'] != 'REMOTE':
                continue
            url = f"https://dnevnik.mos.ru/vcs/links?scheduled_lesson_id={lesson['lesson']['schedule_item_id']}"
            headers = {
                "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                "Auth-token": await self._authenticator.get_token(),
                "Profile-Id": await self._authenticator.get_student_id()
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 204:
                        continue
                    data = await response.json()

            links.append({'lesson': lesson, 'link': data['_embedded']['link_views'][0]['link_url']})

        return links

    async def get_person_details(self):
        profile = await self.get_profile()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/person-details/?contingent_guid={profile['person_id']}&profile_id={await self._authenticator.get_student_id()}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()
                return report

    async def get_schedule(self, date=datetime.now()):
        date_str = date.strftime("%Y-%m-%d")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/schedule/?student_id={await self._authenticator.get_student_id()}&date={date_str}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        report['date'] = datetime.strptime(report['date'], "%Y-%m-%d")

        for activity in report['activities']:
            if activity['begin_utc']:
                activity['begin_utc'] = datetime.fromtimestamp(activity['begin_utc'], tz=timezone.utc)
            if activity['end_utc']:
                activity['end_utc'] = datetime.fromtimestamp(activity['end_utc'], tz=timezone.utc)

        return report

    async def get_schedule_short(self, dates=None):
        if dates is None:
            dates = [datetime.now()]
        date_strs = [date.strftime("%Y-%m-%d") for date in dates]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/schedule/short/?student_id={await self._authenticator.get_student_id()}&dates={','.join(date_strs)}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        for day in report['payload']:
            day['date'] = datetime.strptime(day['date'], "%Y-%m-%d")

        return report['payload']

    async def get_attendance(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/attendance/?student_id={await self._authenticator.get_student_id()}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        for attendance in report['attendance']:
            attendance['date'] = datetime.strptime(attendance['date'], "%Y-%m-%d")

        return report

    async def post_attendance(self, date=datetime.now(), description="болезнь", reason_id=6):
        date_str = date.strftime("%Y-%m-%d")
        data = {
            "student_id": await self._authenticator.get_student_id(),
            "notifications": [{
                "date": date_str,
                "reason_id": reason_id,
                "description": description
            }]
        }
        headers = {
            "x-mes-subsystem": "familymp",
            "auth-token": await self._authenticator.get_token()
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "https://school.mos.ru/api/family/mobile/v1/attendance/",
                    headers=headers,
                    data=json.dumps(data)) as response:
                report = await response.json()
        return report

    async def delete_attendance(self, date=datetime.now()):
        date_str = date.strftime("%Y-%m-%d")
        data = {
            "student_id": await self._authenticator.get_student_id(),
            "notifications": [{
                "date": date_str
            }]
        }
        headers = {
            "x-mes-subsystem": "familymp",
            "auth-token": await self._authenticator.get_token()
        }
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                    "https://school.mos.ru/api/family/mobile/v1/attendance/",
                    headers=headers,
                    data=json.dumps(data)) as response:
                report = await response.json()
        return report

    async def get_homeworks(self, from_date=datetime.now(), to_date=datetime.now()):
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/homeworks/?student_id={await self._authenticator.get_student_id()}&from={from_date_str}&to={to_date_str}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        return report['payload']

    async def get_homeworks_short(self, from_date=datetime.now(), to_date=datetime.now()):
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/homeworks/short?student_id={await self._authenticator.get_student_id()}&from={from_date_str}&to={to_date_str}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        return report['payload']

    async def get_unread_and_important_messages(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    "https://dnevnik.mos.ru/core/api/messages/count_unread_and_important",
                    headers={
                        "Auth-Token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()
        return report

    async def get_menu(self, date=datetime.now()):
        date_str = date.strftime("%Y-%m-%d")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/menu/buffet/?date={date_str}",
                    headers={
                        "x-mes-subsystem": "familymp",
                        "auth-token": await self._authenticator.get_token()
                    }) as response:
                report = await response.json()

        return report['menu']

    async def get_notifications(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/mobile/v1/notifications/search?student_id={await self._authenticator.get_student_id()}",
                    headers={
                        "Auth-token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id(),
                        "x-mes-subsystem": "familymp"
                    }) as response:
                report = await response.json()

        for notification in report:
            notification['datetime'] = datetime.strptime(notification['datetime'], "%Y-%m-%d %H:%M:%S.%f")
            notification['created_at'] = datetime.strptime(notification['created_at'], "%Y-%m-%d %H:%M:%S.%f")
            notification['updated_at'] = datetime.strptime(notification['updated_at'], "%Y-%m-%d %H:%M:%S.%f")

            if notification['event_type'] in ["update_mark", "create_mark"]:
                notification['lesson_date'] = datetime.strptime(notification['lesson_date'], "%Y-%m-%d %H:%M:%S")
            elif notification['event_type'] in ["create_homework", "update_homework"]:
                notification['new_date_assigned_on'] = datetime.strptime(notification['new_date_assigned_on'],
                                                                         "%Y-%m-%d %H:%M:%S")
                notification['new_date_prepared_for'] = datetime.strptime(notification['new_date_prepared_for'],
                                                                          "%Y-%m-%d %H:%M:%S")

        return report

    async def get_visits(self, from_date=datetime.now(), to_date=datetime.now()):
        from_date_str = from_date.astimezone(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d")
        to_date_str = to_date.astimezone(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d")
        profile = await self.get_profile()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/mobile/api/visits?from={from_date_str}&to={to_date_str}&contract_id={profile['ispp_account']}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        for visit in report['payload']:
            visit['date'] = datetime.strptime(visit['date'], "%Y-%m-%d")
            for enter in visit['visits']:
                if ":" in enter['in']:
                    hour, minute = map(int, enter['in'].split(":"))
                    enter['in'] = visit['date'].replace(hour=hour, minute=minute)
                if ":" in enter['out']:
                    hour, minute = map(int, enter['out'].split(":"))
                    enter['out'] = visit['date'].replace(hour=hour, minute=minute)

        return report['payload']

    async def get_billing(self, from_date=datetime.now(), to_date=datetime.now()):
        from_date_str = from_date.astimezone(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d")
        to_date_str = to_date.astimezone(pytz.timezone('Europe/Moscow')).strftime("%Y-%m-%d")
        profile = await self.get_profile()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/mobile/api/billing?from={from_date_str}&to={to_date_str}&contract_id={profile['ispp_account']}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        for bill in report['payload']:
            bill['date'] = datetime.strptime(bill['date'], "%Y-%m-%d")
            for detail in bill['details']:
                detail['time'] = datetime.strptime(bill['date'] + " " + detail['time'], "%Y-%m-%d %H:%M")

        return report

    async def get_progress(self):
        profile = await self.get_profile()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/mobile/api/programs/parallel_curriculum/{profile['curricula']['id']}?student_id={await self._authenticator.get_student_id()}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        return report

    async def get_additional_education_groups(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/ae/api/ae_groups?student_ids={await self._authenticator.get_student_id()}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        return report

    async def get_per_period_marks(self):
        academic_year_id = await self.get_current_academic_year()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/reports/api/progress/json?academic_year_id={academic_year_id}&student_profile_id={await self._authenticator.get_student_id()}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        for subject_mark in report:
            for period in subject_mark['periods']:
                period['start'] = datetime.strptime(period['start_iso'], "%Y-%m-%d")
                period['end'] = datetime.strptime(period['end_iso'], "%Y-%m-%d")

        return report

    async def get_time_periods(self):
        academic_year_id = await self.get_current_academic_year()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://dnevnik.mos.ru/core/api/periods_schedules?academic_year_id={academic_year_id}&student_id={await self._authenticator.get_student_id()}",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()}; student_id={await self._authenticator.get_student_id()};",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id()
                    }) as response:
                report = await response.json()

        for rep in report:
            for period in rep['periods']:
                period['begin_date'] = None if period['begin_date'] is None else datetime.strptime(period['begin_date'],
                                                                                                   "%Y-%m-%d")
                period['end_date'] = None if period['end_date'] is None else datetime.strptime(period['end_date'],
                                                                                               "%Y-%m-%d")

        return report

    async def get_session(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    "https://dnevnik.mos.ru/lms/api/sessions",
                    headers={
                        "Cookie": f"auth_token={await self._authenticator.get_token()};",
                    },
                    data={
                        "auth_token": await self._authenticator.get_token(),
                    }) as response:
                report = await response.json()

        return report

    async def get_school_info(self):
        profile = await self.get_profile()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://school.mos.ru/api/family/web/v1/school_info?class_unit_id={profile['class_unit']['id']}&school_id={profile['school_id']}",
                    headers={
                        "Cookie": "auth_token=" + await self._authenticator.get_token() + "; student_id=" + str(
                            await self._authenticator.get_student_id()) + ";",
                        "Auth-Token": await self._authenticator.get_token(),
                        "Profile-Id": await self._authenticator.get_student_id(),
                        "authorization": await self._authenticator.get_token(),
                        "profile-type": "student",
                        "profile-id": await self._authenticator.get_student_id(),
                        "x-mes-subsystem": "familyweb"
                    }) as response:
                return await response.json()

    @staticmethod
    async def get_academic_years():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dnevnik.mos.ru/core/api/academic_years") as response:
                res = await response.json()

        for year in res:
            year['begin_date'] = datetime.strptime(year['begin_date'], "%y-%m-%d")
            year['end_date'] = datetime.strptime(year['end_date'], "%y-%m-%d")

        return res

    @staticmethod
    async def get_current_academic_year():
        res = await Client.get_academic_years()
        for year in res:
            if year['current_year']:
                return year
        return None
