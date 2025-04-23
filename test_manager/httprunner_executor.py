import json
import time
import httprunner
from httprunner.runner import HttpRunner
import logging

logger = logging.getLogger(__name__)


def execute_test_case(test_case, environment):
    """
    Execute a single test case using HTTPRunner
    """
    try:
        # Prepare the test case for HTTPRunner
        config = {
            "name": test_case.name,
            "base_url": environment.base_url,
            "variables": environment.variables
        }

        # Prepare request
        request = {
            "method": test_case.request_method,
            "url": test_case.request_url,
            "headers": test_case.request_headers,
        }

        if test_case.request_body and test_case.request_method in ['POST', 'PUT', 'PATCH']:
            request["json"] = test_case.request_body

        # Prepare validation
        validate = []
        if test_case.expected_status_code:
            validate.append({"eq": ["status_code", test_case.expected_status_code]})

        for rule in test_case.validation_rules:
            validate.append(rule)

        # Create test step
        test_step = {
            "name": test_case.name,
            "request": request,
            "validate": validate
        }

        # Create test case for HTTPRunner
        http_runner_test_case = {
            "config": config,
            "teststeps": [test_step]
        }

        # Run the test
        start_time = time.time()
        runner = HttpRunner()

        # Check HTTPRunner version to determine the correct method to use
        httprunner_version = getattr(httprunner, "__version__", "unknown")
        logger.info(f"HTTPRunner version: {httprunner_version}")

        # Create a simple mock response in case the test execution fails
        mock_response = {
            "status": "error",
            "response_time": 0,
            "response_status_code": None,
            "response_headers": {},
            "response_body": {},
            "error_message": f"Unable to execute test with HTTPRunner version {httprunner_version}. Please check compatibility."
        }

        # Try to execute the test using different methods based on HTTPRunner version
        try:
            # For HTTPRunner 3.x
            if hasattr(runner, "run"):
                summary = runner.run(http_runner_test_case)
                success = getattr(summary, "success", False)
            # For HTTPRunner 2.x
            elif hasattr(runner, "run_tests"):
                summary = runner.run_tests([http_runner_test_case])
                success = summary.get("success", False)
            # For HTTPRunner 1.x
            elif hasattr(runner, "run_test"):
                summary = runner.run_test(http_runner_test_case)
                success = summary.get("success", False)
            else:
                # Direct HTTP request as fallback
                logger.warning("No compatible HTTPRunner method found. Using fallback HTTP request.")
                import requests

                full_url = f"{environment.base_url.rstrip('/')}/?{test_case.request_url.lstrip('/')}"

                # Prepare request kwargs
                kwargs = {
                    "headers": test_case.request_headers,
                    "timeout": 30
                }

                if test_case.request_body and test_case.request_method in ['POST', 'PUT', 'PATCH']:
                    kwargs["json"] = test_case.request_body

                # Make the request
                response = requests.request(
                    method=test_case.request_method,
                    url=full_url,
                    **kwargs
                )

                # Process response
                try:
                    response_body = response.json()
                except ValueError:
                    response_body = {"content": response.text}

                # Check if status code matches expected
                success = response.status_code == test_case.expected_status_code

                # Create a simple summary
                summary = {
                    "success": success,
                    "response": {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "content": response_body
                    }
                }
        except Exception as e:
            logger.exception(f"Error executing test with HTTPRunner: {e}")
            return mock_response

        end_time = time.time()

        # Process results
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Extract response data based on the summary structure
        try:
            if isinstance(summary, dict):
                # For HTTPRunner 2.x format
                if "details" in summary:
                    step_result = summary.get("details", [{}])[0].get("records", [{}])[0]
                    response_data = step_result.get("meta_data", {}).get("response", {})
                    error_details = step_result.get("attachment", "")
                # For direct HTTP request fallback
                elif "response" in summary:
                    response_data = summary.get("response", {})
                    error_details = ""
                else:
                    response_data = {}
                    error_details = ""
            else:
                # For HTTPRunner 3.x format
                step_results = getattr(summary, "step_results", [])
                if step_results:
                    step_result = step_results[0]
                    response_data = getattr(step_result, "response", {})
                    error_details = getattr(step_result, "error", "")
                else:
                    response_data = {}
                    error_details = getattr(summary, "error", "")
        except Exception as e:
            logger.exception(f"Error processing test results: {e}")
            return mock_response

        # Extract response details
        try:
            if isinstance(response_data, dict):
                response_status_code = response_data.get("status_code")
                response_headers = dict(response_data.get("headers", {}))

                response_content = response_data.get("content", "{}")
                if isinstance(response_content, bytes):
                    response_content = response_content.decode('utf-8')

                if isinstance(response_content, str):
                    try:
                        response_body = json.loads(response_content)
                    except json.JSONDecodeError:
                        response_body = {"content": response_content}
                else:
                    response_body = response_content
            else:
                response_status_code = getattr(response_data, "status_code", None)
                response_headers = dict(getattr(response_data, "headers", {}))

                response_content = getattr(response_data, "content", "{}")
                if isinstance(response_content, bytes):
                    response_content = response_content.decode('utf-8')

                if isinstance(response_content, str):
                    try:
                        response_body = json.loads(response_content)
                    except json.JSONDecodeError:
                        response_body = {"content": response_content}
                else:
                    response_body = response_content
        except Exception as e:
            logger.exception(f"Error extracting response details: {e}")
            return mock_response

        # Determine test status
        status = "passed" if success else "failed"
        error_message = ""

        if not success:
            error_message = error_details if error_details else "Test failed"

        return {
            "status": status,
            "response_time": response_time,
            "response_status_code": response_status_code,
            "response_headers": response_headers,
            "response_body": response_body,
            "error_message": error_message
        }

    except Exception as e:
        logger.exception(f"Error executing test case: {e}")
        return {
            "status": "error",
            "error_message": str(e)
        }


def execute_test_suite(test_suite, environment):
    """
    Execute a test suite (multiple test cases) using HTTPRunner
    """
    results = []

    # Get all test cases in the suite, ordered by their position
    test_suite_cases = test_suite.testsuitecase_set.all().order_by('order')

    for test_suite_case in test_suite_cases:
        test_case = test_suite_case.test_case
        result = execute_test_case(test_case, environment)
        result['test_case_id'] = test_case.id
        results.append(result)

    return results
