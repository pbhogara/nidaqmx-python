import contextlib
import errno
import importlib.resources as pkg_resources
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import urllib.request
import zipfile
from typing import Generator, List, Optional, Tuple

import click

if sys.platform.startswith("win"):
    import winreg
elif sys.platform.startswith("linux"):
    import distro

_logger = logging.getLogger(__name__)

METADATA_FILE = "_installer_metadata.json"


def _get_linux_installation_commands(
    _directory_to_extract_to: str, dist_name: str, dist_version: str, _release_string: str
) -> List[List[str]]:
    """
    Get the installation commands for Linux based on the distribution.

    """
    if dist_name == "ubuntu":
        # Remove "." from dist_version string. 20.04 -> 2004
        _dist_version = dist_version.replace(".", "")
        ubuntu_commands = [
            ["sudo", "apt", "update"],
            [
                "sudo",
                "apt",
                "install",
                f"{_directory_to_extract_to}/NILinux{_release_string}DeviceDrivers/ni-ubuntu{_dist_version}-drivers-{_release_string}.deb",
            ],
            ["sudo", "apt", "update"],
            ["sudo", "apt", "install", "ni-daqmx"],
            ["sudo", "dkms", "autoinstall"],
        ]
        return ubuntu_commands
    elif dist_name == "opensuse":
        _dist_version = dist_version.replace(".", "")
        opensuse_commands = [
            ["sudo", "zypper", "update"],
            ["sudo", "zypper", "install", "insserv"],
            [
                "sudo",
                "zypper",
                "--no-gpg-checks",
                "install",
                f"{_directory_to_extract_to}/NILinux{_release_string}DeviceDrivers/ni-opensuse{_dist_version}-drivers-{_release_string}.rpm",
            ],
            ["sudo", "zypper", "refresh"],
            ["sudo", "zypper", "install", "ni-daqmx"],
            ["sudo", "dkms", "autoinstall"],
        ]
        return opensuse_commands
    elif dist_name == "rhel":
        # Only the major version is needed for rhel. 8.8 -> 8 or 9.2 -> 9
        _dist_version = dist_version.split(".")[0]
        redhat_commands = [
            ["sudo", "yum", "update"],
            ["sudo", "yum", "install", "chkconfig"],
            [
                "sudo",
                "yum",
                "install",
                f"{_directory_to_extract_to}/NILinux{_release_string}DeviceDrivers/ni-rhel{_dist_version}-drivers-{_release_string}.rpm",
            ],
            ["sudo", "yum", "install", "ni-daqmx"],
            ["sudo", "dkms", "autoinstall"],
        ]
        return redhat_commands

    else:
        raise click.ClickException(f"Unsupported distribution '{dist_name}'")


def _parse_version(version: str) -> Tuple[int, ...]:
    """
    Split the version string into a tuple of integers.

    >>> _parse_version("23.8.0")
    (23, 8, 0)
    >>> _parse_version("24.0.0")
    (24, 0, 0)
    >>> _parse_version("invalid_version")
    Traceback (most recent call last):
    ...
    click.exceptions.ClickException: Invalid version format found
    """
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError as e:
        _logger.info("Failed to parse version.", exc_info=True)
        raise click.ClickException(f"Invalid version number '{version}'.") from e


def _get_daqmx_installed_version() -> Optional[str]:
    """
    Check for existing installation of NI-DAQmx.

    """
    if sys.platform.startswith("win"):
        try:
            _logger.debug("Reading the registry entries to get installed DAQmx version")
            with winreg.OpenKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\National Instruments\NI-DAQmx\CurrentVersion",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
            ) as daqmx_reg_key:
                product_name = winreg.QueryValueEx(daqmx_reg_key, "ProductName")[0]
                product_version = winreg.QueryValueEx(daqmx_reg_key, "Version")[0]

            if product_name == "NI-DAQmx":
                _logger.info(
                    "Found registry entries for Product Name: %s and version %s",
                    product_name,
                    product_version,
                )
                return product_version
            return None
        except FileNotFoundError:
            _logger.info("No existing NI-DAQmx installation found.")
            return None
        except PermissionError as e:
            _logger.info("Failed to read the registry key.", exc_info=True)
            raise click.ClickException(
                f"Permission denied while getting the installed NI-DAQmx version.\nDetails: {e}"
            ) from e
        except OSError as e:
            _logger.info("Failed to read the registry key.", exc_info=True)
            raise click.ClickException(
                f"An OS error occurred while getting the installed NI-DAQmx version.\nDetails: {e}"
            ) from e
    elif sys.platform.startswith("linux"):
        try:
            _logger.debug("Checking for installed NI-DAQmx version")
            if distro.id() == "ubuntu":
                dpkg_output = subprocess.run(
                    ["dpkg", "-l", "ni-daqmx"], stdout=subprocess.PIPE
                ).stdout.decode("utf-8")
                version_match = re.search(r"ii\s+ni-daqmx\s+(\d+\.\d+\.\d+)", dpkg_output)
            elif distro.id() == "opensuse" or distro.id() == "rhel":
                rpm_output = subprocess.run(
                    ["rpm", "-q", "ni-daqmx"], stdout=subprocess.PIPE
                ).stdout.decode("utf-8")
                version_match = re.search(r"ni-daqmx-(\d+\.\d+\.\d+)", rpm_output)
            else:
                raise click.ClickException(f"Unsupported distribution '{distro.id()}'")
            if version_match:
                installed_version = version_match.group(1)
                _logger.info("Found installed NI-DAQmx version: %s", installed_version)
                return installed_version
            else:
                _logger.info("No installed NI-DAQmx version found.")
                return None

        except subprocess.CalledProcessError as e:
            _logger.info("Failed to get installed NI-DAQmx version.", exc_info=True)
            raise click.ClickException(
                f"An error occurred while getting the installed NI-DAQmx version.\nCommand returned non-zero exit status '{e.returncode}'."
            ) from e
    else:
        raise NotImplementedError("This function is only supported on Windows and Linux.")


# Creating a temp file that we then close and yield - this is used to allow subprocesses to access
@contextlib.contextmanager
def _multi_access_temp_file(
    *, suffix: str = ".exe", delete: bool = True
) -> Generator[str, None, None]:
    """
    Context manager for creating a temporary file.

    """
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w")
        temp_file.close()
        _logger.debug("Created temp file: %s", temp_file.name)
    except Exception as e:
        _logger.info("Failed to create temporary file.", exc_info=True)
        raise click.ClickException(
            f"Failed to create temporary file '{temp_file.name}'.\nDetails: {e}"
        ) from e

    try:
        yield temp_file.name
    finally:
        if delete:
            try:
                _logger.debug("Deleting temp file: %s", temp_file.name)
                os.unlink(temp_file.name)
            except ValueError as e:
                _logger.info("Failed to delete temporary file.", exc_info=True)
                raise click.ClickException(
                    f"Failed to delete temporary file '{temp_file.name}'.\nDetails: {e}"
                ) from e


@contextlib.contextmanager
def _multi_access_temp_folder(*, delete: bool = True) -> Generator[str, None, None]:
    """
    Context manager for creating a temporary folder.

    """
    try:
        temp_folder = tempfile.TemporaryDirectory()
        _logger.debug("Created temp folder: %s", temp_folder.name)
    except Exception as e:
        _logger.info("Failed to create temporary folder.", exc_info=True)
        raise click.ClickException(
            f"Failed to create temporary folder '{temp_folder.name}'.\nDetails: {e}"
        ) from e

    try:
        yield temp_folder.name
    finally:
        if delete:
            try:
                _logger.debug("Deleting temp folder: %s", temp_folder.name)
                shutil.rmtree(temp_folder.name)
            except ValueError as e:
                _logger.info("Failed to delete temporary folder.", exc_info=True)
                raise click.ClickException(
                    f"Failed to delete temporary folder '{temp_folder.name}'.\nDetails: {e}"
                ) from e


def _load_data(
    json_data: str, platform: str
) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    """
    Load data from JSON string and extract Windows metadata.

    >>> _load_data('{"Windows": [{"Location": "path/to/driver", "Version": "1.0"}]}')
    ('path/to/driver', '1.0')

    >>> _load_data('{"Windows": [{"Location": "path/to/driver"}]}')
    Traceback (most recent call last):
    ...
    click.exceptions.ClickException: Unable to fetch driver details.

    >>> _load_data('{"Linux": [{"Location": "path/to/driver", "Version": "1.0"}]}')
    Traceback (most recent call last):
    ...
    click.exceptions.ClickException: Unable to fetch driver details.

    """
    try:
        if platform == "Windows":
            metadata = json.loads(json_data).get("Windows", [])
        elif platform == "Linux":
            metadata = json.loads(json_data).get("Linux", [])
        else:
            raise click.ClickException(f"Unsupported os '{platform}'")
    except json.JSONDecodeError as e:
        _logger.info("Failed to parse the json data.", exc_info=True)
        raise click.ClickException(f"Failed to parse the driver metadata.\nDetails: {e}") from e

    for metadata_entry in metadata:
        location: Optional[str] = metadata_entry.get("Location")
        version: Optional[str] = metadata_entry.get("Version")
        release: Optional[str] = metadata_entry.get("Release")
        supported_os: Optional[List[str]] = metadata_entry.get("supportedOS")
        _logger.debug("From metadata file found location %s and version %s.", location, version)
        if location and version:
            return location, version, release, supported_os
    raise click.ClickException(f"Unable to fetch driver details")


def _get_driver_details(platform: str) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    """
    Parse the JSON data and retrieve the download link and version information.

    """
    try:
        with pkg_resources.open_text(__package__, METADATA_FILE) as json_file:
            _logger.debug("Opening the metadata file %s.", METADATA_FILE)
            location, version, release, supported_os = _load_data(json_file.read(), platform)
        return location, version, release, supported_os

    except click.ClickException:
        raise
    except Exception as e:
        _logger.info("Failed to get driver metadata.", exc_info=True)
        raise click.ClickException(
            f"An error occurred while getting the driver metadata.\nDetails: {e}"
        ) from e


def _install_daqmx_driver_windows(download_url: str) -> None:
    """
    Download and launch NI-DAQmx Driver installation in an interactive mode

    """
    temp_file = None
    try:
        with _multi_access_temp_file() as temp_file:
            _logger.info("Downloading Driver to %s", temp_file)
            urllib.request.urlretrieve(download_url, temp_file)
            _logger.info("Installing NI-DAQmx")
            subprocess.run([temp_file], shell=True, check=True)
    except subprocess.CalledProcessError as e:
        _logger.info("Failed to install NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(
            f"An error occurred while installing the NI-DAQmx driver. Command returned non-zero exit status '{e.returncode}'."
        ) from e
    except urllib.error.URLError as e:
        _logger.info("Failed to download NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(f"Failed to download the NI-DAQmx driver.\nDetails: {e}") from e
    except Exception as e:
        _logger.info("Failed to install NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(f"Failed to install the NI-DAQmx driver.\nDetails: {e}") from e


def _install_daqmx_driver_linux(download_url: str, release: str) -> None:
    """
    Download NI Linux Device Drivers and install NI-DAQmx on Linux OS

    """
    try:
        with _multi_access_temp_file(suffix=".zip") as temp_file:
            _logger.info("Downloading Driver to %s", temp_file)
            urllib.request.urlretrieve(download_url, temp_file)

            with _multi_access_temp_folder() as temp_folder:
                _directory_to_extract_to = temp_folder

                _logger.info("Unzipping the downloaded file to %s", _directory_to_extract_to)

                with zipfile.ZipFile(temp_file, "r") as zip_ref:
                    zip_ref.extractall(_directory_to_extract_to)

                _logger.info("Installing NI-DAQmx")
                for command in _get_linux_installation_commands(
                    _directory_to_extract_to, distro.id(), distro.version(), release
                ):
                    print("\nRunning command:", " ".join(command))
                    subprocess.run(command, check=True)

        # Check if the installation was successful
        if not _get_daqmx_installed_version():
            raise click.ClickException(
                "Failed to install NI-DAQmx driver. All installation commands ran successfully but the driver is not installed."
            )
        else:
            print("NI-DAQmx driver installed successfully.")

    except subprocess.CalledProcessError as e:
        _logger.info("Failed to install NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(
            f"An error occurred while installing the NI-DAQmx driver. Command returned non-zero exit status '{e.returncode}'."
        ) from e
    except urllib.error.URLError as e:
        _logger.info("Failed to download NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(f"Failed to download the NI-DAQmx driver.\nDetails: {e}") from e
    except Exception as e:
        _logger.info("Failed to install NI-DAQmx driver.", exc_info=True)
        raise click.ClickException(f"Failed to install the NI-DAQmx driver.\nDetails: {e}") from e


def _ask_user_confirmation(user_message: str) -> bool:
    """
    Prompt for user confirmation

    """
    while True:
        response = input(user_message + " (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("Please enter 'yes' or 'no'.")


def _confirm_and_upgrade_daqmx_driver(
    latest_version: str,
    installed_version: str,
    download_url: str,
    release: str,
) -> None:
    """
    Confirm with the user and upgrade the NI-DAQmx driver if necessary.

    """
    _logger.debug("Entering _confirm_and_upgrade_daqmx_driver")
    latest_parts: Tuple[int, ...] = _parse_version(latest_version)
    installed_parts: Tuple[int, ...] = _parse_version(installed_version)
    if installed_parts >= latest_parts:
        print(
            f"Installed NI-DAQmx version ({installed_version}) is up to date. (Expected {latest_version} or newer.)"
        )
        return
    is_upgrade = _ask_user_confirmation(
        f"Installed NI-DAQmx version is {installed_version}. Latest version available is {latest_version}. Do you want to upgrade?"
    )
    if is_upgrade:
        if sys.platform.startswith("win"):
            _install_daqmx_driver_windows(download_url)
        elif sys.platform == "linux":
            _install_daqmx_driver_linux(download_url, release)


def _install_daqmx_windows_driver() -> None:
    """
    Install the NI-DAQmx driver on Windows.

    """
    installed_version = _get_daqmx_installed_version()
    download_url, latest_version, release, supported_os = _get_driver_details("Windows")
    if not download_url:
        raise click.ClickException(f"Failed to fetch the download url.")
    else:
        if installed_version and latest_version:
            _confirm_and_upgrade_daqmx_driver(
                latest_version, installed_version, download_url, release
            )
        else:
            _install_daqmx_driver_windows(download_url)


def _is_distribution_supported() -> None:
    """
    Raises an exception if the linux distribution and its version are not supported.

    """
    dist_name = distro.id()
    dist_version = distro.version()

    # For rhel, we only need the major version
    if dist_name == "rhel":
        dist_version = dist_version.split(".")[0]
    dist_name_and_version = dist_name + " " + dist_version

    download_url, latest_version, release, supported_os = _get_driver_details("Linux")

    # Check if the platform is one of the supported ones
    if dist_name_and_version in supported_os:
        _logger.info(f"The platform is supported: {dist_name_and_version}")
    else:
        raise click.ClickException(f"The platform {dist_name_and_version} is not supported.")


def _install_daqmx_linux_driver() -> None:
    """
    Install the NI-DAQmx driver on Linux.

    """

    installed_version = _get_daqmx_installed_version()
    download_url, latest_version, release, supported_os = _get_driver_details("Linux")

    try:
        _is_distribution_supported()
    except Exception as e:
        raise click.ClickException(f"Distribution not supported.\nDetails: {e}") from e

    if not download_url:
        raise click.ClickException(f"Failed to fetch the download url.")
    else:
        if installed_version and latest_version:
            _confirm_and_upgrade_daqmx_driver(
                latest_version, installed_version, download_url, release
            )
        else:
            _install_daqmx_driver_linux(download_url, release)


def installdriver() -> None:
    """
    Download and launch NI-DAQmx Driver installation in an interactive mode.

    """
    try:
        if sys.platform.startswith("win"):
            _logger.info("Windows platform detected")
            _install_daqmx_windows_driver()
        elif sys.platform.startswith("linux"):
            _logger.info("Linux platform detected")
            _install_daqmx_linux_driver()
        else:
            raise click.ClickException(
                f"The 'installdriver' command is supported only on Windows and Linux."
            )
    except click.ClickException:
        raise
    except Exception as e:
        _logger.info("Failed to install driver.", exc_info=True)
        raise click.ClickException(
            f"An error occurred during the installation of the NI-DAQmx driver.\nDetails: {e}"
        ) from e
