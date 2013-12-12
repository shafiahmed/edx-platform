*******************************************
Content experiments
*******************************************

This is a brief overview of the support for content experiments in the platform.

For now, there is only one type of experiment: content split testing.  This lets course authors define an experiment with several _experimental conditions_, add xblocks that reference that experiment in various places in the course, and specify what content students in each experimental condition should see.  The LMS provides a way to randomly assign students to experimental conditions for each experiment, so that they see the right content at runtime.

Where the code is:


common:

split_test_module -- a block that has one child per experimental condition (could be a vertical or other container with more blocks inside), and config specifying which child corresponds to which condition.
course_module -- a course has a list of experiments, each of which specifies the number 

LMS:
  runtime--LmsExperimentSupport mixin.  Provides a way for split_test_modules to get the experimental condition for a user in the lms.
  experiment djangoapp--provides a simple service-like API for the above.  Does the random assignment of studens to experimental conditions, and persists the results.

Things to watch out for (some not implemented yet):
- grade export needs to be smarter, because different students can see different graded things
- grading needs to only grade the children that a particular student sees (so if there are problems in both conditions in a split_test, any student would see only one set)
- ui -- icons in sequences need to be passed through
  - tooltips need to be passed through
- author changes post-release: conditions can be added or deleted after an experiment is live.  This is usually a bad idea, but can be useful, so it's allowed.  Need to handle all the cases.
- analytics logging around this is important.  
 
