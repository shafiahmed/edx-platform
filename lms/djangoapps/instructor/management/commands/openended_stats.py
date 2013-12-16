from xmodule.open_ended_grading_classes.openendedchild import OpenEndedChild
from courseware.models import StudentModule
from student.models import anonymous_id_for_user
from ...utils import get_descriptor, get_module_for_student, get_enrolled_students, create_csv_from_student_anonymous_ids
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Admin command for open ended problems."""

    help = "Usage: openended_stats <course_id> <problem_location> \n"

    def handle(self, *args, **options):
        """Handler for command."""

        print "args = ", args

        if len(args) == 2:
            course_id = args[0]
            location = args[1]
        else:
            print self.help
            return

        descriptor = get_descriptor(course_id, location)
        if descriptor is None:
            print "Location not found in course"
            return

        enrolled_students = get_enrolled_students(course_id)
        print "Total students enrolled: {0}".format(enrolled_students.count())

        self.get_state_counts(enrolled_students, course_id, location)

    def get_state_counts(self, students, course_id, location):
        """Print stats of students."""

        stats = {
            OpenEndedChild.INITIAL: 0,
            OpenEndedChild.ASSESSING: 0,
            OpenEndedChild.POST_ASSESSMENT: 0,
            OpenEndedChild.DONE: 0
        }

        student_anonymous_ids = []
        student_modules = StudentModule.objects.filter(student__in=students)
        print "Total student modules: {0}".format(students.count())
        for index, student_module in enumerate(student_modules):
            if index % 100 == 0:
                print "{0} students processed".format(index)

            module = get_module_for_student(student_module.student, course_id, location)
            latest_task = module._xmodule.child_module.get_current_task()
            stats[latest_task.child_state] += 1
            if latest_task.child_state == OpenEndedChild.ASSESSING:
                student_anonymous_ids.append(anonymous_id_for_user(student_module.student, course_id))

        #Create a csv of student anonymous ids.
        if student_anonymous_ids:
            create_csv_from_student_anonymous_ids(student_anonymous_ids)

        print stats
