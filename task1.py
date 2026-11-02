
import requests
from packaging.requirements import Requirement
from packaging.version import Version
from packaging.specifiers import SpecifierSet

PYTHON_VERSION = Version("3.11")
PYPI_URL = "https://pypi.org/pypi"


def check_package(line):
    try:
        requirement = Requirement(line)
        name = requirement.name
        version = str(requirement.specifier)

        # Get exact requested version from PyPI
        url = f"{PYPI_URL}/{name}/{version.replace('==', '')}/json"
        response = requests.get(url, timeout=15)

        if response.status_code == 404:
            # Check whether the package itself exists
            package_response = requests.get(
                f"{PYPI_URL}/{name}/json", timeout=15
            )

            if package_response.status_code == 404:
                return "not_found", name, None

            return "version_not_found", name, None

        response.raise_for_status()
        data = response.json()

        # Check Python 3.11 compatibility
        files = data.get("urls", [])
        python_rules = [
            item.get("requires_python")
            for item in files
            if item.get("requires_python")
        ]

        if not python_rules:
            return "unknown", name, None

        compatible = any(
            SpecifierSet(rule).contains(PYTHON_VERSION)
            for rule in python_rules
        )

        if compatible:
            return "compatible", name, Version(data["info"]["version"])

        return "incompatible", name, Version(data["info"]["version"])

    except Exception as error:
        print(f"Error checking {line}: {error}")
        return "error", line, None


def main():

    # Read requirements file
    with open("requirements.txt", "r", encoding="utf-8") as file:
        dependencies = [
            line.strip()
            for line in file
            if line.strip() and not line.strip().startswith("#")
        ]

    not_found = []
    incompatible = []
    version_not_found = []
    valid_versions = []

    # Check every dependency
    for dependency in dependencies:

        status, name, version = check_package(dependency)

        if status == "not_found":
            not_found.append(name)

        elif status == "incompatible":
            incompatible.append(name)

        # elif status == "version_not_found":
        #     version_not_found.append(name)

        elif status in ("compatible", "unknown"):
            if version is not None:
                valid_versions.append((name, version))

    # Find highest pinned version
    highest = max(valid_versions, key=lambda item: item[1]) if valid_versions else None

    # Print required output
    print("Dependencies checked:", len(dependencies))

    print("Not found on PyPI:")
    for name in not_found:
        print(name)
    if not not_found:
        print("None")

    print("Incompatible with Python 3.11:")
    for name in incompatible:
        print(name)
    if not incompatible:
        print("None")

    print("Highest requirement:")
    if highest:
        print(f"{highest[0]}=={highest[1]}")
    else:
        print("None")

    if version_not_found:
        print("Requested versions not found:")
        for name in version_not_found:
            print(name)


if __name__ == "__main__":
    main()
