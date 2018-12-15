import asyncio
import logging
import binascii
import socket
import os.path
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.core import callback
# from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA, STATE_OFF, STATE_IDLE, STATE_HEAT, STATE_COOL, STATE_AUTO,
# ATTR_OPERATION_MODE, SUPPORT_OPERATION_MODE, SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE)
from homeassistant.components.remote import (
    ATTR_ACTIVITY, ATTR_DELAY_SECS, ATTR_DEVICE, ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS, DOMAIN, PLATFORM_SCHEMA)
from homeassistant.const import (ATTR_UNIT_OF_MEASUREMENT, ATTR_TEMPERATURE, CONF_NAME, CONF_HOST, CONF_MAC, CONF_TIMEOUT, CONF_CUSTOMIZE)
from homeassistant.helpers.event import (async_track_state_change)
from homeassistant.helpers.entity import Entity
from configparser import ConfigParser
from base64 import b64encode, b64decode

REQUIREMENTS = ['broadlink==0.9.0']

_LOGGER = logging.getLogger(__name__)

CONF_IRCODES_INI = 'ircodes_ini'
CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'
CONF_TARGET_TEMP = 'target_temp'
CONF_TARGET_TEMP_STEP = 'target_temp_step'
CONF_TEMP_SENSOR = 'temp_sensor'
CONF_OPERATIONS = 'operations'
CONF_FAN_MODES = 'fan_modes'
CONF_DEFAULT_OPERATION = 'default_operation'
CONF_DEFAULT_FAN_MODE = 'default_fan_mode'

CONF_DEFAULT_OPERATION_FROM_IDLE = 'default_operation_from_idle'

DEFAULT_NAME = 'Broadlink IR Climate'
DEFAULT_TIMEOUT = 10
DEFAULT_RETRY = 3
DEFAULT_MIN_TEMP = 16
DEFAULT_MAX_TEMP = 30
DEFAULT_TARGET_TEMP = 20
DEFAULT_TARGET_TEMP_STEP = 1
DEFAULT_FAN_MODE_LIST = ['low', 'mid', 'high', 'auto']
DEFAULT_OPERATION = 'off'
DEFAULT_FAN_MODE = 'auto'


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Broadlink IR Climate platform."""
    name = config.get(CONF_NAME)
    ip_addr = config.get(CONF_HOST)
    mac_addr = binascii.unhexlify(config.get(CONF_MAC).encode().replace(b':', b''))
    
    
    import broadlink
    
    broadlink_device = broadlink.rm((ip_addr, 80), mac_addr, None)
    broadlink_device.timeout = config.get(CONF_TIMEOUT)

    try:
        broadlink_device.auth()
    except socket.timeout:
        _LOGGER.error("Failed to connect to Broadlink RM Device")
    
    
    ircodes_ini_file = config.get(CONF_IRCODES_INI)
    
    if ircodes_ini_file.startswith("/"):
        ircodes_ini_file = ircodes_ini_file[1:]
        
    ircodes_ini_path = hass.config.path(ircodes_ini_file)
    
    if os.path.exists(ircodes_ini_path):
        ircodes_ini = ConfigParser()
        ircodes_ini.read(ircodes_ini_path)
    else:
        _LOGGER.error("The ini file was not found. (" + ircodes_ini_path + ")")
        return
    
    async_add_devices([
        BroadlinkIRTV('Remote Two', True, 'mdi:remote')
    ])

class BroadlinkIRTV(RemoteDevice):
    """Representation of a demo remote."""

    def __init__(self, name, state, icon):
        """Initialize the Demo Remote."""
        self._name = name or DEVICE_DEFAULT_NAME
        self._state = state
        self._icon = icon
        self._last_command_sent = None

    @property
    def should_poll(self):
        """No polling needed for a demo remote."""
        return False

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return self._icon

    @property
    def is_on(self):
        """Return true if remote is on."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device state attributes."""
        if self._last_command_sent is not None:
            return {'last_command_sent': self._last_command_sent}

    def turn_on(self, **kwargs):
        """Turn the remote on."""
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the remote off."""
        self._state = False
        self.schedule_update_ha_state()

    def send_command(self, command, **kwargs):
        """Send a command to a device."""
        for com in command:
            self._last_command_sent = com
        self.schedule_update_ha_state()
