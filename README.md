# ESB Lights

Home Assistant integration for the Kinetic weathervane lights. Creates a sensor
carrying tonight's Empire State Building colour scheme, so automations and the
dashboard card read Home Assistant state instead of each making their own HTTP
call.

Pairs with [esblights-card](https://github.com/KineticTeam/esblights-card) for
the display, and with the internal API in
[esblights-nodejs](https://github.com/KineticTeam/esblights-nodejs).

## Install

**HACS → ⋮ → Custom repositories**, add this repo with category **Integration**,
then install it and restart Home Assistant.

**Settings → Devices & Services → Add Integration → ESB Lights**, then fill in:

| Field | Value |
|---|---|
| API address | `192.168.123.114:4000` |
| API key | your key, or blank if the API doesn't require one |
| Check for a new colour every | `3600` seconds |

The address is validated before the entry is created, so a typo or an
unreachable host is reported in the dialog rather than failing silently later.
A bare `host:port` is fine — `http://` is assumed, and pasting the full
`/api/esb-light-data` URL works too.

## What you get

`sensor.esb_lights_color`

| | |
|---|---|
| State | the colour description, e.g. `purple` |
| `hexCodes` | `["#9B27D6"]` |
| `xyzCodes` | `[[x, y, brightness]]` — the shape `light.turn_on` wants |
| `reason` | the occasion, e.g. *In Honor of…* |

Change the poll interval later via **Configure** on the integration; no need to
remove and re-add.

## Driving lights from it

`xyzCodes` is already in Home Assistant's format:

```yaml
- service: light.turn_on
  target:
    entity_id: light.weathervane
  data:
    xy_color: "{{ state_attr('sensor.esb_lights_color','xyzCodes')[0][:2] }}"
    brightness: "{{ (state_attr('sensor.esb_lights_color','xyzCodes')[0][2] * 254) | round | int }}"
```

See `packages/esb_lights.yaml` in the main repo for the full cycling automation,
sunset trigger and unreachable-API alert.

## Notes

The API is internal-only by design. Home Assistant must be on a network that can
reach it — if setup reports "couldn't reach the API", that's usually a firewall
or VLAN boundary rather than a wrong address.
