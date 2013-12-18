from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from courseware.models import StudentModule
from student.models import anonymous_id_for_user
from ...utils import get_descriptor, get_module_for_student, get_enrolled_students, create_csv_from_student_anonymous_ids
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Admin command for open ended problems."""

    help = "Usage: openended_stats <course_id> <problem_location> \n"
    output_transaction = True

    def handle(self, *args, **options):
        """Handler for command."""

        if len(args) == 2:
            course_id = args[0]
            location = args[1]
        else:
            print self.help
            return

        descriptor = get_descriptor(course_id, location)
        if descriptor is None:
            print "Location {0} not found in course".format(location)
            return

        try:
            enrolled_students = get_enrolled_students(course_id)
            print "Total students enrolled in {0}: {1}".format(course_id, enrolled_students.count())

            self.get_state_counts(enrolled_students, course_id, location)

        except KeyboardInterrupt:
            print "\nOperation Cancelled"

    def get_state_counts(self, students, course_id, location):
        """Print stats of students."""

        stats = {
            OpenEndedChild.INITIAL: 0,
            OpenEndedChild.ASSESSING: 0,
            OpenEndedChild.POST_ASSESSMENT: 0,
            OpenEndedChild.DONE: 0
        }

        students_with_saved_answers = []
        students_with_submissions = []
        students_with_invalid_state = []

        student_modules = StudentModule.objects.filter(module_state_key=location, student__in=students)
        print "Total student modules: {0}".format(student_modules.count())

        for index, student_module in enumerate(student_modules):
            student = student_module.student
            if index % 100 == 0:
                print "{0} students processed".format(index)

            module = get_module_for_student(student, course_id, location)
            if module is None:
                print "WARNING: No state found."
                students_with_invalid_state.append(student)
                continue

            latest_task = module._xmodule.child_module.get_current_task()
            if latest_task is None:
                print "WARNING: No state found."
                students_with_invalid_state.append(student)
                continue

            stats[latest_task.child_state] += 1

            if latest_task.child_state == OpenEndedChild.INITIAL:
                if latest_task.stored_answer is not None:
                    students_with_saved_answers.append(student)
            if latest_task.child_state == OpenEndedChild.ASSESSING:
                students_with_submissions.append(student)

        #Create a csv of student anonymous ids.
        create_csv_from_student_anonymous_ids([anonymous_id_for_user(student, course_id) for student in students_with_saved_answers], "students_with_saved_answers")
        create_csv_from_student_anonymous_ids([anonymous_id_for_user(student, course_id) for student in students_with_submissions], "students_with_submissions")

        print "Errors for {0} students.".format(len(students_with_invalid_state))
        print "----------------------------------"
        print "Viewed the problem: {0}".format(stats[OpenEndedChild.INITIAL] - len(students_with_saved_answers))
        print "Saved answers: {0}".format(len(students_with_saved_answers))
        print "Submitted but have not received grades: {0}".format(stats[OpenEndedChild.ASSESSING])
        print "Received grades: {0}".format(stats[OpenEndedChild.POST_ASSESSMENT] + stats[OpenEndedChild.DONE])
        print "----------------------------------"
