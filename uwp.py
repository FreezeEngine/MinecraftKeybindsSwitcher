# Get-AppxPackage
# Based on https://gist.github.com/ueffel/41dcb16102ee3c40a98d4a57b072ace6

import subprocess


class AppXPackage(object):
    def __init__(self, property_dict):
        self.Name = None
        self.Version = None
        for key, value in property_dict.items():
            setattr(self, key, value)
        self.application = self._get_application()

    def _get_application(self):
        app = AppX(self.Name, self.Version)
        return app


class AppX(object):
    def __init__(self, name=None, version=None):
        self.name = name
        self.version = version


def get_minecraft_version():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    output, err = subprocess.Popen(['C:\\windows\\system32\\windowspowershell\\v1.0\\powershell.exe',
                                    'mode con cols=512; Get-AppxPackage *Minecraft*'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True,
                                   shell=False,
                                   startupinfo=startupinfo).communicate()

    packages = []
    temp = {}
    for package in output.strip().split('\n\n'):
        for line in package.splitlines():
            line_parts = line.split(":")
            key = line_parts[0].strip()
            value = ":".join(line_parts[1:]).strip()
            temp[key] = value
        package = AppXPackage(temp)
        if package.application:
            packages.append(package)

    for app in packages:
        return app.application.version
