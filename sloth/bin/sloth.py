import sys
from os.path import dirname, realpath
sys.path.insert(0, dirname(dirname(dirname(realpath(__file__)))))
from PyQt5.QtWidgets import QApplication
from sloth.core.labeltool import LabelTool
from sloth import APP_NAME, ORGANIZATION_NAME, ORGANIZATION_DOMAIN


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setApplicationName(APP_NAME)

    labeltool = LabelTool()
    sys.exit(app.exec_())