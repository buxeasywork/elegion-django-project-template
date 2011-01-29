"""
Test runner with code coverage.
Falls back to django simple runner if coverate-lib not installed
"""
import os

from django.test.utils import get_runner
from django.conf import settings


class dummy_settings():
    TEST_RUNNER = settings.COVERATE_TEST_RUNNER \
        if hasattr(settings, 'COVERATE_TEST_RUNNER') else 'django.test.simple.run_tests'
inner_runner = get_runner(dummy_settings)


try:
    from coverage import coverage as Coverage
except ImportError:
    run_tests = inner_runner
else:
    coverage = Coverage()
    def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
        coverage.start()
        test_results = inner_runner(test_labels, verbosity, interactive, extra_tests)
        coverage.stop()

        #collect all submodules of app to build coverage only on test_labels apps
        coverage_modules = []
        for app in test_labels:
            try:
                module = __import__(app, globals(), locals(), [''])
            except ImportError:
                # two cases
                #  * last part is TestCase name, so coverage in this case not needed
                #  * real import error, test runners fails and coverage not needed too
                coverage_modules = None
                break
            if module:
                base_path = os.path.join(os.path.split(module.__file__)[0], "")
                for root, dirs, files in os.walk(base_path):
                    for fname in files:
                        if fname.endswith(".py") and os.path.getsize(os.path.join(root, fname)) > 1:
                            try:
                                mname = os.path.join(app, os.path.join(root, fname).replace(base_path, ""))
                                coverage_modules.append(mname)
                            except ImportError:
                                pass #do nothing

        if coverage_modules or not test_labels:
            coverage.html_report(coverage_modules, directory=settings.COVERAGE_REPORT_PATH)

        return test_results

