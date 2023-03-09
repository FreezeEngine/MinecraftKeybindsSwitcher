# Get-AppxPackage
# explorer.exe shell:appsFolder\put-your-PackageFamilyName-here!put-your-app-ID-here

import subprocess
import os
import xml.etree.ElementTree as etree
import re
import ctypes as ct


class AppXPackage(object):
    def __init__(self, property_dict):
        for key, value in property_dict.items():
            setattr(self, key, value)
        self.applications = self._get_applications()

    def _get_applications(self):
        manifest_path = os.path.join(self.InstallLocation, 'AppxManifest.xml')
        if not os.path.isfile(manifest_path):
            return []
        manifest = etree.parse(manifest_path)
        ns = {'default': re.sub(r'\{(.*?)\}.+', r'\1', manifest.getroot().tag)}

        package_applications = manifest.findall('./default:Applications/default:Application', ns)
        if not package_applications:
            return []

        apps = []

        package_identity = None
        package_identity_node = manifest.find('./default:Identity', ns)
        if package_identity_node is not None:
            package_identity = package_identity_node.get('Name')

        description = None
        description_node = manifest.find('./default:Properties/default:Description', ns)
        if description_node is not None:
            description = description_node.text

        display_name = None
        display_name_node = manifest.find('./default:Properties/default:DisplayName', ns)
        if display_name_node is not None:
            display_name = display_name_node.text

        icon = None
        logo_node = manifest.find('./default:Properties/default:DisplayName', ns)
        if logo_node is not None:
            logo = logo_node.text
            icon_path = os.path.join(self.InstallLocation, logo)

        for application in package_applications:
            if display_name and display_name.startswith('ms-resource:'):
                resource = self._get_resource(
                    '@{{{}\\resources.pri? ms-resource://{}/resources/{}}}'.format(self.InstallLocation,
                                                                                   package_identity,
                                                                                   display_name[len('ms-resource:'):]))
                if resource is not None:
                    display_name = resource
                else:
                    continue

            if description and description.startswith('ms-resource:'):
                resource = self._get_resource(
                    '@{{{}\\resources.pri? ms-resource://{}/resources/{}}}'.format(self.InstallLocation,
                                                                                   package_identity,
                                                                                   description[len('ms-resource:'):]))
                if resource is not None:
                    description = resource
                else:
                    continue

            apps.append(
                AppX(['explorer.exe', 'shell:AppsFolder\{}!{}'.format(self.PackageFamilyName, application.get('Id'))],
                     display_name,
                     description,
                     icon_path, self.Version))
        return apps

    @staticmethod
    def _get_resource(resource_descriptor):
        input = ct.create_unicode_buffer(resource_descriptor)
        output = ct.create_unicode_buffer(1024)
        size = ct.sizeof(output)
        input_ptr = ct.pointer(input)
        output_ptr = ct.pointer(output)
        result = ct.windll.shlwapi.SHLoadIndirectString(input_ptr, output_ptr, size, None)
        if result == 0:
            return output.value
        else:
            return None


class AppX(object):
    def __init__(self, execution=[], display_name=None, description=None, icon_path=None, version=None):
        self.execution = execution
        self.display_name = display_name
        self.description = description
        self.icon_path = icon_path
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
        if package.applications:
            packages.append(package)

    for app in packages:
        return app.applications[0].version


if __name__ == '__main__':
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
        if package.applications:
            packages.append(package)

    for app in packages:
        if 'Minecraft' in app.applications[0].display_name:
            print(app.applications[0].__dict__)
        print('App: "{}" v{} ({}) -> {}'.format(app.applications[0].display_name,
                                                app.applications[0].version,
                                                app.applications[0].description,
                                                ' '.join(app.applications[0].execution)))
