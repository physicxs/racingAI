#!/usr/bin/env python3
"""
Decoder Validation Test

Generates the SAME packets as Java UDPPacketSender and verifies
that f1_receiver.py decodes them correctly.

No game or Java required — pure unit test of the Python decoder.
"""

import struct
import math
import sys

# Import decoder functions
from f1_receiver import (
    decode_header, decode_motion, decode_lap_data, decode_car_telemetry,
    decode_session, SessionState, MAX_CARS, HEADER_SIZE
)

# ─── Constants matching Java UDPPacketSender ─────────────────────────────────

TRACK_LENGTH = 5303.0
RADIUS_X = 400.0
RADIUS_Z = 250.0
CENTER_X = 0.0
CENTER_Z = 0.0
TRACK_HEIGHT = 5.0
SPEED_MPS = 80.0
DT = 0.033


def compute_lap_distance(frame_id, car_index):
    offset = car_index * 200.0
    return ((frame_id * SPEED_MPS * DT) + offset) % TRACK_LENGTH


def compute_world_position(lap_distance):
    angle = (lap_distance / TRACK_LENGTH) * 2.0 * math.pi
    x = CENTER_X + RADIUS_X * math.cos(angle)
    z = CENTER_Z + RADIUS_Z * math.sin(angle)
    return (x, TRACK_HEIGHT, z)


def write_header(packet_id, frame_id, buf=None):
    return struct.pack('<HBBBBBQfIIBB',
        2025,           # packetFormat
        25,             # gameYear
        1,              # gameMajorVersion
        0,              # gameMinorVersion
        1,              # packetVersion
        packet_id,      # packetId
        123456789,      # sessionUID
        frame_id * 0.033,  # sessionTime
        frame_id,       # frameIdentifier
        frame_id,       # overallFrameIdentifier
        0,              # playerCarIndex
        255,            # secondaryPlayerCarIndex
    )


def build_motion_packet(frame_id):
    """Build motion packet matching Java UDPPacketSender.sendMotionPacket()"""
    data = write_header(0, frame_id)
    for i in range(22):
        lap_dist = compute_lap_distance(frame_id, i)
        x, y, z = compute_world_position(lap_dist)
        data += struct.pack('<ffffff',
            x, y, z,          # worldPosition
            50.0, 0.0, 70.0,  # worldVelocity
        )
        data += struct.pack('<hhhhhh',
            0, 0, 32767,      # forwardDir
            32767, 0, 0,      # rightDir
        )
        data += struct.pack('<ffffff',
            0.5, 1.2, -0.3,   # gForce
            0.1, 0.0, 0.0,    # yaw, pitch, roll
        )
    return data


def build_lap_packet(frame_id):
    """Build lap data packet matching Java UDPPacketSender.sendLapDataPacket()"""
    data = write_header(2, frame_id)
    for i in range(22):
        lap_dist = compute_lap_distance(frame_id, i)
        lap_num = int((frame_id * SPEED_MPS * DT + i * 200.0) / TRACK_LENGTH) + 1
        data += struct.pack('<II', 90000 + i * 1000, 30000)  # lastLapTime, currentLapTime
        data += struct.pack('<HB', 15000, 0)  # sector1
        data += struct.pack('<HB', 16000, 0)  # sector2
        data += struct.pack('<HB', 0, 0)      # deltaToCarInFront
        data += struct.pack('<HB', i * 500, 0)  # deltaToRaceLeader
        data += struct.pack('<fff', lap_dist, 5000.0, 0.0)  # lapDist, totalDist, scDelta
        data += struct.pack('<BBBBBBBBBBBBB',
            i + 1,   # carPosition
            lap_num, # currentLapNum
            0, 0, 0, 0, 0, 0, 0, 0, 0,  # pit/sector/penalties/warnings
            i + 6,   # gridPosition
            4,       # driverStatus (on track)
        )
        data += struct.pack('<B', 2)  # resultStatus
        data += struct.pack('<B', 0)  # pitLaneTimerActive
        data += struct.pack('<HH', 0, 0)  # pitLaneTime, pitStopTimer
        data += struct.pack('<B', 0)  # pitStopShouldServePen
        data += struct.pack('<f', 320.5)  # speedTrapFastestSpeed
        data += struct.pack('<B', 3)  # speedTrapFastestLap
    data += struct.pack('<BB', 255, 255)  # timeTrialPBCarIdx, timeTrialRivalCarIdx
    return data


def build_telemetry_packet(frame_id):
    """Build telemetry packet matching Java UDPPacketSender.sendTelemetryPacket()"""
    data = write_header(6, frame_id)
    for i in range(22):
        data += struct.pack('<H', 250 + i * 5)  # speed
        data += struct.pack('<fff', 0.8, 0.0, 0.0)  # throttle, steer, brake
        data += struct.pack('<Bb', 0, 7)  # clutch, gear
        data += struct.pack('<H', 12000)  # engineRPM
        data += struct.pack('<BB', 0, 50)  # drs, revLightsPercent
        data += struct.pack('<H', 0)  # revLightsBitValue
        data += struct.pack('<HHHH', 450, 450, 450, 450)  # brakesTemp
        data += struct.pack('<BBBB', 85, 85, 85, 85)  # tyresSurfaceTemp
        data += struct.pack('<BBBB', 90, 90, 90, 90)  # tyresInnerTemp
        data += struct.pack('<H', 95)  # engineTemp
        data += struct.pack('<ffff', 23.5, 23.5, 23.5, 23.5)  # tyresPressure
        data += struct.pack('<BBBB', 0, 0, 0, 0)  # surfaceType
    data += struct.pack('<BBb', 255, 255, 0)  # mfd panels, suggestedGear
    return data


def build_session_packet(frame_id):
    """Build session packet matching Java UDPPacketSender.sendSessionPacket()"""
    data = write_header(1, frame_id)
    data += struct.pack('<bbbBHBbBHHBBBBB',
        0,      # weather
        25,     # trackTemp
        22,     # airTemp
        5,      # totalLaps
        5303,   # trackLength
        12,     # sessionType
        0,      # trackId (Melbourne)
        0,      # formula
        3600,   # sessionTimeLeft
        3600,   # sessionDuration
        80,     # pitSpeedLimit
        0,      # gamePaused
        0,      # isSpectating
        255,    # spectatorCarIndex
        1,      # sliProNativeSupport
    )
    # Safety car after marshal zones: numMarshalZones=0 then safetyCarStatus
    data += struct.pack('<B', 0)  # numMarshalZones
    data += struct.pack('<BB', 0, 0)  # safetyCarStatus, networkGame
    # Pad rest
    data += b'\x00' * 600
    return data


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_header():
    print("Test: Header parsing...")
    data = build_motion_packet(100)
    h = decode_header(data)
    assert h['packet_format'] == 2025, f"packetFormat: {h['packet_format']}"
    assert h['game_year'] == 25
    assert h['packet_id'] == 0
    assert h['session_uid'] == 123456789
    assert h['frame_identifier'] == 100
    assert h['player_car_index'] == 0
    print("  PASS")


def test_motion():
    print("Test: Motion packet decoding...")
    state = SessionState()
    frame_id = 100

    data = build_motion_packet(frame_id)
    header = decode_header(data)
    decode_motion(data, state, header)

    errors = 0
    for i in range(22):
        car = state.cars[i]
        lap_dist = compute_lap_distance(frame_id, i)
        ex, ey, ez = compute_world_position(lap_dist)

        dx = abs(car.world_position_x - ex)
        dy = abs(car.world_position_y - ey)
        dz = abs(car.world_position_z - ez)

        if dx > 0.01 or dy > 0.01 or dz > 0.01:
            print(f"  FAIL car {i}: expected ({ex:.2f}, {ey:.2f}, {ez:.2f}) "
                  f"got ({car.world_position_x:.2f}, {car.world_position_y:.2f}, {car.world_position_z:.2f})")
            errors += 1

        if abs(car.g_force_lateral - 0.5) > 0.01:
            print(f"  FAIL car {i}: gForceLateral expected 0.5 got {car.g_force_lateral}")
            errors += 1
        if abs(car.yaw - 0.1) > 0.01:
            print(f"  FAIL car {i}: yaw expected 0.1 got {car.yaw}")
            errors += 1

    if errors == 0:
        print(f"  PASS (all 22 cars, positions + gForce + rotation)")
    return errors


def test_lap_data():
    print("Test: Lap data decoding...")
    state = SessionState()
    frame_id = 100

    data = build_lap_packet(frame_id)
    header = decode_header(data)
    decode_lap_data(data, state, header)

    errors = 0
    for i in range(22):
        car = state.cars[i]
        expected_pos = i + 1
        expected_dist = compute_lap_distance(frame_id, i)
        expected_delta = i * 500 / 1000.0  # ms → seconds

        if car.car_position != expected_pos:
            print(f"  FAIL car {i}: position expected {expected_pos} got {car.car_position}")
            errors += 1
        if abs(car.lap_distance - expected_dist) > 0.1:
            print(f"  FAIL car {i}: lapDistance expected {expected_dist:.1f} got {car.lap_distance:.1f}")
            errors += 1
        if abs(car.delta_to_race_leader_seconds - expected_delta) > 0.01:
            print(f"  FAIL car {i}: delta expected {expected_delta:.2f} got {car.delta_to_race_leader_seconds:.2f}")
            errors += 1
        if car.driver_status != 4:
            print(f"  FAIL car {i}: driverStatus expected 4 got {car.driver_status}")
            errors += 1
        if car.grid_position != i + 6:
            print(f"  FAIL car {i}: gridPosition expected {i+6} got {car.grid_position}")
            errors += 1

    if errors == 0:
        print(f"  PASS (all 22 cars: position, lapDistance, delta, status, grid)")
    return errors


def test_telemetry():
    print("Test: Telemetry decoding...")
    state = SessionState()
    frame_id = 100

    data = build_telemetry_packet(frame_id)
    header = decode_header(data)
    decode_car_telemetry(data, state, header)

    errors = 0
    for i in range(22):
        car = state.cars[i]
        expected_speed = 250 + i * 5

        if car.speed != expected_speed:
            print(f"  FAIL car {i}: speed expected {expected_speed} got {car.speed}")
            errors += 1
        if abs(car.throttle - 0.8) > 0.01:
            print(f"  FAIL car {i}: throttle expected 0.8 got {car.throttle}")
            errors += 1
        if car.gear != 7:
            print(f"  FAIL car {i}: gear expected 7 got {car.gear}")
            errors += 1
        if car.engine_rpm != 12000:
            print(f"  FAIL car {i}: engineRPM expected 12000 got {car.engine_rpm}")
            errors += 1
        if car.brakes_temperature != [450, 450, 450, 450]:
            print(f"  FAIL car {i}: brakesTemp expected [450,450,450,450] got {car.brakes_temperature}")
            errors += 1
        if car.tyres_surface_temperature != [85, 85, 85, 85]:
            print(f"  FAIL car {i}: tyresSurfTemp expected [85,85,85,85] got {car.tyres_surface_temperature}")
            errors += 1
        if abs(car.tyres_pressure[0] - 23.5) > 0.01:
            print(f"  FAIL car {i}: tyresPressure[0] expected 23.5 got {car.tyres_pressure[0]}")
            errors += 1

    if errors == 0:
        print(f"  PASS (all 22 cars: speed, throttle, gear, RPM, temps, pressure)")
    return errors


def test_session():
    print("Test: Session decoding...")
    state = SessionState()
    frame_id = 100

    data = build_session_packet(frame_id)
    header = decode_header(data)
    decode_session(data, state, header)

    errors = 0
    if state.track_id != 0:
        print(f"  FAIL: trackId expected 0 got {state.track_id}")
        errors += 1
    if state.track_length != 5303:
        print(f"  FAIL: trackLength expected 5303 got {state.track_length}")
        errors += 1
    if state.weather != 0:
        print(f"  FAIL: weather expected 0 got {state.weather}")
        errors += 1
    if state.track_temperature != 25:
        print(f"  FAIL: trackTemp expected 25 got {state.track_temperature}")
        errors += 1
    if state.air_temperature != 22:
        print(f"  FAIL: airTemp expected 22 got {state.air_temperature}")
        errors += 1
    if state.total_laps != 5:
        print(f"  FAIL: totalLaps expected 5 got {state.total_laps}")
        errors += 1
    if state.safety_car_status != 0:
        print(f"  FAIL: safetyCarStatus expected 0 got {state.safety_car_status}")
        errors += 1

    if errors == 0:
        print(f"  PASS (trackId, trackLength, weather, temps, laps, safetyCar)")
    return errors


def test_full_pipeline():
    print("Test: Full pipeline (all packet types → JSON output)...")
    from f1_receiver import generate_snapshot

    state = SessionState()
    frame_id = 100

    # Feed all packet types
    for builder, decoder in [
        (build_motion_packet, decode_motion),
        (build_lap_packet, decode_lap_data),
        (build_telemetry_packet, decode_car_telemetry),
        (build_session_packet, decode_session),
    ]:
        data = builder(frame_id)
        header = decode_header(data)
        decoder(data, state, header)

    # Generate snapshot
    snapshot = generate_snapshot(state)
    if snapshot is None:
        print("  FAIL: snapshot is None")
        return 1

    import json
    frame = json.loads(snapshot)

    errors = 0

    # Check player (car 0)
    p = frame['player']
    if p['speed'] != 250:
        print(f"  FAIL: player.speed expected 250 got {p['speed']}")
        errors += 1
    if p['position'] != 1:
        print(f"  FAIL: player.position expected 1 got {p['position']}")
        errors += 1
    if abs(p['throttle'] - 0.8) > 0.01:
        print(f"  FAIL: player.throttle expected 0.8 got {p['throttle']}")
        errors += 1
    if p['gear'] != 7:
        print(f"  FAIL: player.gear expected 7 got {p['gear']}")
        errors += 1

    # Check world position matches expected
    ex, ey, ez = compute_world_position(compute_lap_distance(frame_id, 0))
    wp = p['world_pos_m']
    if abs(wp['x'] - ex) > 0.1 or abs(wp['z'] - ez) > 0.1:
        print(f"  FAIL: player.world_pos expected ({ex:.1f}, {ez:.1f}) got ({wp['x']:.1f}, {wp['z']:.1f})")
        errors += 1

    # Check allCars
    ac = frame['allCars']
    if len(ac) != 21:  # 22 - 1 player
        print(f"  FAIL: allCars count expected 21 got {len(ac)}")
        errors += 1

    # Check meta
    m = frame['meta']
    if m['track_id'] != 0:
        print(f"  FAIL: meta.track_id expected 0 got {m['track_id']}")
        errors += 1

    if errors == 0:
        print(f"  PASS (full pipeline: packets → state → JSON)")
    return errors


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("F1 2025 Python Decoder Validation")
    print("=" * 60)
    print()

    total_errors = 0
    total_errors += test_header() or 0
    total_errors += test_motion()
    total_errors += test_lap_data()
    total_errors += test_telemetry()
    total_errors += test_session()
    total_errors += test_full_pipeline()

    print()
    print("=" * 60)
    if total_errors == 0:
        print("ALL TESTS PASSED — decoder matches Java UDPPacketSender exactly")
    else:
        print(f"FAILED: {total_errors} errors found")
    print("=" * 60)

    sys.exit(1 if total_errors else 0)


if __name__ == '__main__':
    main()
