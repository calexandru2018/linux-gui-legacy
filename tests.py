import os
import shutil
from queue import Queue

from app.presenters.login_presenter import LoginPresenter
from app.presenters.settings_presenter import SettingsPresenter

from app.services.login_service import LoginService
from app.services.settings_service import SettingsService

from app.constants import GUI_CONFIG_DIR
from protonvpn_cli.constants import CONFIG_DIR

q = Queue()

login_service = LoginService()
login_presenter = LoginPresenter(login_service, q)

settings_service = SettingsService()
settings_presenter = SettingsPresenter(settings_service, q)

# def test_login():
#     if os.path.isdir(GUI_CONFIG_DIR):
#         shutil.rmtree(GUI_CONFIG_DIR)

#     if os.path.isdir(CONFIG_DIR):
#         shutil.rmtree(CONFIG_DIR)

#     arg = dict(
#         username_field="test", 
#         password_field="test",
#         member_free_radio=1,
#         member_basic_radio=0,
#         member_plus_radio=0,
#         member_visionary_radio=0
#     )
#     assert login_presenter.on_login(**arg) == True

# def test_user_pass():
#     arg = dict(username="test2", password="test2")
#     assert settings_presenter.update_user_pass(**arg) == True

# def test_dns():
#     list = ["1", "0"]
#     for arg in list:
#         assert settings_presenter.update_dns(arg) == True

# def test_pvpn_plan():
#     list = [dict(tier=i) for i in range(1,5)]
#     for arg in list:
#         assert settings_presenter.update_pvpn_plan(**arg) == True

# def test_procotol():
#     list = ["udp", "tcp"]
#     for arg in list:
#         assert settings_presenter.update_def_protocol(arg) == True

# def test_connect_preference():
#     list = [
#         [dict(user_choice="dis", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="fast", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="rand", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="p2p", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="sc", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="tor", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="PT", country_display="TEST", quick_connect=True), True],
#         [dict(user_choice="testing", country_display="TEST", quick_connect=True), False],
#         # [dict(user_choice="PT", country_display="TEST"), True],
#         # [dict(user_choice="ES", country_display="TEST"), True],
#         # [dict(user_choice="SE", country_display="TEST"), True],
#         # [dict(user_choice="testing", country_display="TEST"), False],
#     ]
#     for arg in list:
#         assert settings_presenter.update_connect_preference(**arg[0]) == arg[1]

# def test_killswitch():
#     list = ["0", "1"]
#     for arg in list:
#         assert settings_presenter.update_killswitch(arg) == True

# def test_split_tunn_status():
#     list = ["0", "1"]
#     for arg in list:
#         assert settings_presenter.update_killswitch(arg) == True

# def test_add_ips():
#     """Checks that valid IP's are added and that invalid IPs are filtered
#     """
#     list = [
#         [dict(split_tunneling_content="192.168.1.0"), True],
#         [dict(split_tunneling_content="255.255.255.255"), True],
#         [dict(split_tunneling_content="192.168.1.0asdasdasd2"), False],
#         [dict(split_tunneling_content="192.168.1."), False],
#         [dict(split_tunneling_content="192.168.1. \n 192.12312,312"), False],
#     ]
#     for arg in list:
#         assert settings_presenter.update_split_tunneling(**arg[0]) == arg[1]

# def test_tray_disply_configurations():
#     list = [
#         dict(setting_value=1, setting_display="tray_data_tx_combobox"),
#         dict(setting_value=0, setting_display="tray_data_tx_combobox"),
#         #
#         dict(setting_value=1, setting_display="tray_servername_combobox"),
#         dict(setting_value=0, setting_display="tray_servername_combobox"),
#         #
#         dict(setting_value=1, setting_display="tray_time_connected_combobox"),
#         dict(setting_value=0, setting_display="tray_time_connected_combobox"),
#         #
#         dict(setting_value=1, setting_display="tray_serverload_combobox"),
#         dict(setting_value=0, setting_display="tray_serverload_combobox"),
#     ]
#     for arg in list:
#         assert settings_presenter.update_tray_display(**arg) == True

# def test_purge():
#     assert settings_presenter.purge_configurations() == True