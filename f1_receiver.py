#!/usr/bin/env python3
"""
F1 2025 Telemetry Receiver (Python)

Behavior-preserving port of the Java telemetry ingestion system.
Receives F1 2025 UDP packets, decodes them, merges state, selects
nearby cars, and outputs JSONL to stdout at 30 Hz.

Usage:
    python3 f1_receiver.py                    # Live UDP on port 20777
    python3 f1_receiver.py --port 20778       # Custom port
    python3 f1_receiver.py --replay raw.bin   # Replay raw UDP dump
"""

import json
import socket
import struct
import sys
import threading
import time

# ─── Configuration ────────────────────────────────────────────────────────────

UDP_PORT = 20777
MAX_PACKET_SIZE = 2048
OUTPUT_RATE_HZ = 30
MAX_CARS = 22
NEARBY_MAX = 6
NEARBY_TIME_GAP = 1.5
NEARBY_AHEAD_PREFERRED = 4
NEARBY_BEHIND_PREFERRED = 2

# Packet IDs
PID_MOTION = 0
PID_SESSION = 1
PID_LAP_DATA = 2
PID_CAR_TELEMETRY = 6
PID_CAR_STATUS = 7
PID_CAR_DAMAGE = 10

# Header: 29 bytes
HEADER_FMT = '<HBBBBBQfIIBB'
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 29

# Per-car struct formats
MOTION_FMT = '<ffffffhhhhhhffffff'
MOTION_SIZE = struct.calcsize(MOTION_FMT)  # 60

LAP_FMT = '<IIHBHBHBHBfffBBBBBBBBBBBBBBBHHBfB'
LAP_SIZE = struct.calcsize(LAP_FMT)  # 57

TELEM_FMT = '<HfffBbHBBHHHHHBBBBBBBBHffffBBBB'
TELEM_SIZE = struct.calcsize(TELEM_FMT)  # 60

STATUS_FMT = '<BBBBBfffHHBBHBBBbfffBfffB'
STATUS_SIZE = struct.calcsize(STATUS_FMT)  # 55

DAMAGE_FMT = '<ffffBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB'
# tyresWear[4]=16, tyresDamage[4]=4, brakesDamage[4]=4, tyreBlisters[4]=4,
# then 18 uint8 fields = 18. Total = 16+4+4+4+18 = 46
DAMAGE_SIZE = 46


# ─── Track Names ──────────────────────────────────────────────────────────────

TRACK_NAMES = {
    -1: "Unknown", 0: "Melbourne (Australia)", 1: "Paul Ricard (France)",
    2: "Shanghai (China)", 3: "Sakhir (Bahrain)", 4: "Catalunya (Spain)",
    5: "Monaco", 6: "Montreal (Canada)", 7: "Silverstone (Great Britain)",
    8: "Hockenheim (Germany)", 9: "Hungaroring (Hungary)", 10: "Spa (Belgium)",
    11: "Monza (Italy)", 12: "Singapore", 13: "Suzuka (Japan)",
    14: "Abu Dhabi (UAE)", 15: "Texas (USA)", 16: "Brazil", 17: "Austria",
    18: "Sochi (Russia)", 19: "Mexico", 20: "Baku (Azerbaijan)",
    21: "Sakhir Short", 22: "Silverstone Short", 23: "Texas Short",
    24: "Suzuka Short", 25: "Hanoi (Vietnam)", 26: "Zandvoort (Netherlands)",
    27: "Imola (Italy)", 28: "Portimão (Portugal)", 29: "Jeddah (Saudi Arabia)",
    30: "Miami (USA)", 31: "Las Vegas (USA)", 32: "Losail (Qatar)",
}


# ─── Car State ────────────────────────────────────────────────────────────────

class CarState:
    __slots__ = [
        'car_index',
        # Motion
        'world_position_x', 'world_position_y', 'world_position_z',
        'world_velocity_x', 'world_velocity_y', 'world_velocity_z',
        'g_force_lateral', 'g_force_longitudinal', 'g_force_vertical',
        'yaw', 'pitch', 'roll',
        # Lap
        'last_lap_time_ms', 'current_lap_time_ms',
        'lap_distance', 'total_distance',
        'car_position', 'current_lap_num', 'grid_position', 'driver_status',
        'delta_to_race_leader_seconds',
        # Telemetry
        'speed', 'gear', 'throttle', 'steer', 'brake',
        'engine_rpm', 'engine_temperature',
        'tyres_pressure', 'drs',
        'tyres_surface_temperature', 'tyres_inner_temperature',
        'brakes_temperature',
        # Damage
        'tyres_wear', 'front_left_wing_damage', 'front_right_wing_damage',
        'rear_wing_damage', 'floor_damage', 'diffuser_damage', 'sidepod_damage',
        'tyres_damage',
        # Status
        'drs_allowed', 'ers_deploy_mode',
        'actual_tyre_compound', 'visual_tyre_compound', 'tyres_age_laps',
        'ers_store_energy', 'ers_deployed_this_lap',
        'ers_harvested_this_lap_mguk', 'ers_harvested_this_lap_mguh',
        'vehicle_fia_flags',
    ]

    def __init__(self, car_index):
        self.car_index = car_index
        # Motion
        self.world_position_x = 0.0
        self.world_position_y = 0.0
        self.world_position_z = 0.0
        self.world_velocity_x = 0.0
        self.world_velocity_y = 0.0
        self.world_velocity_z = 0.0
        self.g_force_lateral = 0.0
        self.g_force_longitudinal = 0.0
        self.g_force_vertical = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        # Lap
        self.last_lap_time_ms = 0
        self.current_lap_time_ms = 0
        self.lap_distance = 0.0
        self.total_distance = 0.0
        self.car_position = 0
        self.current_lap_num = 0
        self.grid_position = 0
        self.driver_status = 0
        self.delta_to_race_leader_seconds = 0.0
        # Telemetry
        self.speed = 0
        self.gear = 0
        self.throttle = 0.0
        self.steer = 0.0
        self.brake = 0.0
        self.engine_rpm = 0
        self.engine_temperature = 0
        self.tyres_pressure = [0.0, 0.0, 0.0, 0.0]
        self.drs = 0
        self.tyres_surface_temperature = [0, 0, 0, 0]
        self.tyres_inner_temperature = [0, 0, 0, 0]
        self.brakes_temperature = [0, 0, 0, 0]
        # Damage
        self.tyres_wear = [0.0, 0.0, 0.0, 0.0]
        self.front_left_wing_damage = 0.0
        self.front_right_wing_damage = 0.0
        self.rear_wing_damage = 0.0
        self.floor_damage = 0
        self.diffuser_damage = 0
        self.sidepod_damage = 0
        self.tyres_damage = [0, 0, 0, 0]
        # Status
        self.drs_allowed = 0
        self.ers_deploy_mode = 0
        self.actual_tyre_compound = 0
        self.visual_tyre_compound = 0
        self.tyres_age_laps = 0
        self.ers_store_energy = 0.0
        self.ers_deployed_this_lap = 0.0
        self.ers_harvested_this_lap_mguk = 0.0
        self.ers_harvested_this_lap_mguh = 0.0
        self.vehicle_fia_flags = 0

    def is_active(self):
        return 1 <= self.driver_status <= 4


# ─── Session State ────────────────────────────────────────────────────────────

class SessionState:
    def __init__(self):
        self.cars = [CarState(i) for i in range(MAX_CARS)]
        self.player_car_index = 0
        self.session_uid = 0
        self.session_time = 0.0
        self.frame_identifier = 0
        self.track_id = None
        self.track_length = None
        self.safety_car_status = 0
        self.weather = 0
        self.track_temperature = 0
        self.air_temperature = 0
        self.total_laps = 0
        self.lock = threading.Lock()


# ─── Packet Decoder ───────────────────────────────────────────────────────────

def decode_header(data):
    """Decode 29-byte packet header. Returns dict or None."""
    if len(data) < HEADER_SIZE:
        return None
    fields = struct.unpack_from(HEADER_FMT, data, 0)
    return {
        'packet_format': fields[0],
        'game_year': fields[1],
        'game_major_version': fields[2],
        'game_minor_version': fields[3],
        'packet_version': fields[4],
        'packet_id': fields[5],
        'session_uid': fields[6],
        'session_time': fields[7],
        'frame_identifier': fields[8],
        'overall_frame_identifier': fields[9],
        'player_car_index': fields[10],
        'secondary_player_car_index': fields[11],
    }


def decode_motion(data, state, header):
    """Decode motion packet for all 22 cars."""
    offset = HEADER_SIZE
    with state.lock:
        for i in range(MAX_CARS):
            if offset + MOTION_SIZE > len(data):
                break
            f = struct.unpack_from(MOTION_FMT, data, offset)
            car = state.cars[i]
            car.world_position_x = f[0]
            car.world_position_y = f[1]
            car.world_position_z = f[2]
            car.world_velocity_x = f[3]
            car.world_velocity_y = f[4]
            car.world_velocity_z = f[5]
            # f[6]-f[11] = direction vectors (not used in output)
            car.g_force_lateral = f[12]
            car.g_force_longitudinal = f[13]
            car.g_force_vertical = f[14]
            car.yaw = f[15]
            car.pitch = f[16]
            car.roll = f[17]
            offset += MOTION_SIZE
        _update_meta(state, header)


def decode_lap_data(data, state, header):
    """Decode lap data for all 22 cars."""
    offset = HEADER_SIZE
    with state.lock:
        for i in range(MAX_CARS):
            if offset + LAP_SIZE > len(data):
                break
            f = struct.unpack_from(LAP_FMT, data, offset)
            car = state.cars[i]
            car.last_lap_time_ms = f[0]
            car.current_lap_time_ms = f[1]
            # f[2]=sector1MSPart, f[3]=sector1MinPart
            # f[4]=sector2MSPart, f[5]=sector2MinPart
            # f[6]=deltaToCarInFrontMSPart, f[7]=deltaToCarInFrontMinPart
            delta_leader_ms = f[8]   # deltaToRaceLeaderMSPart (uint16)
            delta_leader_min = f[9]  # deltaToRaceLeaderMinutesPart (uint8)
            car.delta_to_race_leader_seconds = delta_leader_min * 60.0 + delta_leader_ms / 1000.0
            car.lap_distance = f[10]
            car.total_distance = f[11]
            # f[12]=safetyCarDelta
            car.car_position = f[13]
            car.current_lap_num = f[14]
            # f[15]=pitStatus, f[16]=numPitStops, f[17]=sector
            # f[18]=currentLapInvalid, f[19]=penalties
            # f[20]=totalWarnings, f[21]=cornerCuttingWarnings
            # f[22]=numUnservedDriveThrough, f[23]=numUnservedStopGo
            car.grid_position = f[24]
            car.driver_status = f[25]
            # f[26]=resultStatus, f[27]=pitLaneTimerActive
            # f[28]=pitLaneTimeInLaneInMS, f[29]=pitStopTimerInMS
            # f[30]=pitStopShouldServePen
            # f[31]=speedTrapFastestSpeed, f[32]=speedTrapFastestLap
            offset += LAP_SIZE
        _update_meta(state, header)


def decode_car_telemetry(data, state, header):
    """Decode telemetry for all 22 cars."""
    offset = HEADER_SIZE
    with state.lock:
        for i in range(MAX_CARS):
            if offset + TELEM_SIZE > len(data):
                break
            f = struct.unpack_from(TELEM_FMT, data, offset)
            car = state.cars[i]
            car.speed = f[0]
            car.throttle = f[1]
            car.steer = f[2]
            car.brake = f[3]
            # f[4]=clutch
            car.gear = f[5]
            car.engine_rpm = f[6]
            car.drs = f[7]
            # f[8]=revLightsPercent, f[9]=revLightsBitValue
            car.brakes_temperature = [f[10], f[11], f[12], f[13]]
            car.tyres_surface_temperature = [f[14], f[15], f[16], f[17]]
            car.tyres_inner_temperature = [f[18], f[19], f[20], f[21]]
            car.engine_temperature = f[22]
            car.tyres_pressure = [f[23], f[24], f[25], f[26]]
            # f[27]-f[30] = surfaceType[4]
            offset += TELEM_SIZE
        _update_meta(state, header)


def decode_car_status(data, state, header):
    """Decode status for all 22 cars."""
    offset = HEADER_SIZE
    with state.lock:
        for i in range(MAX_CARS):
            if offset + STATUS_SIZE > len(data):
                break
            f = struct.unpack_from(STATUS_FMT, data, offset)
            car = state.cars[i]
            # f[0]=tractionControl, f[1]=antiLockBrakes, f[2]=fuelMix
            # f[3]=frontBrakeBias, f[4]=pitLimiterStatus
            # f[5]=fuelInTank, f[6]=fuelCapacity, f[7]=fuelRemainingLaps
            # f[8]=maxRPM, f[9]=idleRPM, f[10]=maxGears
            car.drs_allowed = f[11]
            # f[12]=drsActivationDistance
            car.actual_tyre_compound = f[13]
            car.visual_tyre_compound = f[14]
            car.tyres_age_laps = f[15]
            car.vehicle_fia_flags = f[16]
            # f[17]=enginePowerICE, f[18]=enginePowerMGUK
            car.ers_store_energy = f[19]
            car.ers_deploy_mode = f[20]
            car.ers_harvested_this_lap_mguk = f[21]
            car.ers_harvested_this_lap_mguh = f[22]
            car.ers_deployed_this_lap = f[23]
            # f[24]=networkPaused
            offset += STATUS_SIZE
        _update_meta(state, header)


def decode_car_damage(data, state, header):
    """Decode damage for all 22 cars."""
    offset = HEADER_SIZE
    with state.lock:
        for i in range(MAX_CARS):
            if offset + DAMAGE_SIZE > len(data):
                break
            # Read tyresWear[4] as floats
            tw = struct.unpack_from('<ffff', data, offset)
            off2 = offset + 16
            # Read remaining 30 uint8 fields
            rest = struct.unpack_from('<' + 'B' * 30, data, off2)
            car = state.cars[i]
            car.tyres_wear = list(tw)
            car.tyres_damage = [rest[0], rest[1], rest[2], rest[3]]
            # brakesDamage = rest[4:8], tyreBlisters = rest[8:12]
            car.front_left_wing_damage = float(rest[12])
            car.front_right_wing_damage = float(rest[13])
            car.rear_wing_damage = float(rest[14])
            car.floor_damage = rest[15]
            car.diffuser_damage = rest[16]
            car.sidepod_damage = rest[17]
            # rest[18]=drsFault, rest[19]=ersFault
            # rest[20]=gearBoxDamage, rest[21]=engineDamage
            # rest[22-29] = engine wear fields, blown, seized
            offset += DAMAGE_SIZE
        _update_meta(state, header)


def decode_session(data, state, header):
    """Decode session packet."""
    offset = HEADER_SIZE
    if offset + 18 > len(data):
        return
    with state.lock:
        f = struct.unpack_from('<bbbBHBbBHHBBBBB', data, offset)
        state.weather = f[0]
        state.track_temperature = f[1]
        state.air_temperature = f[2]
        state.total_laps = f[3]
        state.track_length = f[4]
        # f[5]=sessionType
        state.track_id = f[6]
        # f[7]=formula, f[8]=sessionTimeLeft, f[9]=sessionDuration
        # f[10]=pitSpeedLimit, f[11]=gamePaused, f[12]=isSpectating
        # f[13]=spectatorCarIndex, f[14]=sliProNativeSupport
        # Skip marshal zones (1 byte numMarshalZones + 21 * 5 bytes)
        mz_offset = offset + 18
        if mz_offset < len(data):
            num_mz = struct.unpack_from('<B', data, mz_offset)[0]
            sc_offset = mz_offset + 1 + num_mz * 5
            if sc_offset + 2 <= len(data):
                sc_fields = struct.unpack_from('<BB', data, sc_offset)
                state.safety_car_status = sc_fields[0]
                # sc_fields[1] = networkGame
        _update_meta(state, header)


def _update_meta(state, header):
    """Update session metadata from packet header (must be called inside lock)."""
    state.session_uid = header['session_uid']
    state.session_time = header['session_time']
    state.frame_identifier = header['frame_identifier']
    state.player_car_index = header['player_car_index']


# Decoder dispatch table
DECODERS = {
    PID_MOTION: decode_motion,
    PID_SESSION: decode_session,
    PID_LAP_DATA: decode_lap_data,
    PID_CAR_TELEMETRY: decode_car_telemetry,
    PID_CAR_STATUS: decode_car_status,
    PID_CAR_DAMAGE: decode_car_damage,
}


def process_packet(data, state):
    """Decode a raw UDP packet and update state."""
    header = decode_header(data)
    if header is None:
        return
    if header['packet_format'] != 2025:
        return
    pid = header['packet_id']
    decoder = DECODERS.get(pid)
    if decoder:
        decoder(data, state, header)


# ─── Nearby Cars Selection ────────────────────────────────────────────────────

def select_nearby_cars(state):
    """Select up to 6 nearby cars. Returns list of (car, gap) tuples."""
    player_idx = state.player_car_index
    if player_idx < 0 or player_idx >= MAX_CARS:
        return []
    player = state.cars[player_idx]
    if not player.is_active():
        return []

    player_delta = player.delta_to_race_leader_seconds
    cars_ahead = []
    cars_behind = []

    for car in state.cars:
        if car.car_index == player_idx:
            continue
        if not car.is_active():
            continue
        gap = car.delta_to_race_leader_seconds - player_delta
        if abs(gap) > NEARBY_TIME_GAP:
            continue
        if gap < 0:
            cars_ahead.append((car, gap))
        else:
            cars_behind.append((car, gap))

    # Sort: ahead by delta ascending (closest to leader first)
    cars_ahead.sort(key=lambda x: x[0].delta_to_race_leader_seconds)
    # Sort: behind by delta ascending (closest to player first)
    cars_behind.sort(key=lambda x: x[0].delta_to_race_leader_seconds)

    ahead_count = min(NEARBY_AHEAD_PREFERRED, len(cars_ahead))
    behind_count = min(NEARBY_BEHIND_PREFERRED, len(cars_behind))

    # Fill remaining slots
    total = ahead_count + behind_count
    if total < NEARBY_MAX:
        remaining = NEARBY_MAX - total
        extra_ahead = min(remaining, len(cars_ahead) - ahead_count)
        ahead_count += extra_ahead
        remaining -= extra_ahead
        if remaining > 0:
            extra_behind = min(remaining, len(cars_behind) - behind_count)
            behind_count += extra_behind

    result = []
    for i in range(ahead_count):
        result.append(cars_ahead[i])
    for i in range(behind_count):
        result.append(cars_behind[i])
    return result


# ─── JSON Output ──────────────────────────────────────────────────────────────

def generate_snapshot(state):
    """Generate JSON snapshot matching Java output format."""
    with state.lock:
        player_idx = state.player_car_index
        if player_idx < 0 or player_idx >= MAX_CARS:
            return None
        player = state.cars[player_idx]
        if not player.is_active():
            return None

        # Meta
        meta = {
            'track_id': state.track_id,
            'track_length': state.track_length,
            'safety_car': state.safety_car_status,
            'weather': state.weather,
            'track_temp': state.track_temperature,
            'air_temp': state.air_temperature,
            'total_laps': state.total_laps,
        }

        # Player
        player_data = {
            'position': player.car_position,
            'lapNumber': player.current_lap_num,
            'lapDistance': player.lap_distance,
            'speed': player.speed,
            'gear': player.gear,
            'throttle': player.throttle,
            'brake': player.brake,
            'steering': player.steer,
            'tyreWear': {
                'rearLeft': player.tyres_wear[0],
                'rearRight': player.tyres_wear[1],
                'frontLeft': player.tyres_wear[2],
                'frontRight': player.tyres_wear[3],
            },
            'world_pos_m': {
                'x': player.world_position_x,
                'y': player.world_position_y,
                'z': player.world_position_z,
            },
            'yaw': player.yaw,
            'pitch': player.pitch,
            'roll': player.roll,
            'gForceLateral': player.g_force_lateral,
            'gForceLongitudinal': player.g_force_longitudinal,
            'drs': player.drs,
            'drsAllowed': player.drs_allowed,
            'ersDeployMode': player.ers_deploy_mode,
            'ersStoreEnergy': player.ers_store_energy,
            'ersDeployedThisLap': player.ers_deployed_this_lap,
            'ersHarvestedThisLapMGUK': player.ers_harvested_this_lap_mguk,
            'ersHarvestedThisLapMGUH': player.ers_harvested_this_lap_mguh,
            'tyreSurfaceTemp': list(player.tyres_surface_temperature),
            'tyreInnerTemp': list(player.tyres_inner_temperature),
            'tyreCompound': player.actual_tyre_compound,
            'tyreCompoundVisual': player.visual_tyre_compound,
            'tyresAgeLaps': player.tyres_age_laps,
            'tyreDamage': list(player.tyres_damage),
            'brakeTemp': list(player.brakes_temperature),
            'frontLeftWingDamage': player.front_left_wing_damage,
            'frontRightWingDamage': player.front_right_wing_damage,
            'rearWingDamage': player.rear_wing_damage,
            'floorDamage': player.floor_damage,
            'diffuserDamage': player.diffuser_damage,
            'sidepodDamage': player.sidepod_damage,
            'vehicleFiaFlags': player.vehicle_fia_flags,
        }

        # Nearby cars
        nearby = select_nearby_cars(state)
        nearby_data = []
        for car, gap in nearby:
            nearby_data.append({
                'carIndex': car.car_index,
                'position': car.car_position,
                'gap': round(gap, 3),
                'world_pos_m': {
                    'x': car.world_position_x,
                    'y': car.world_position_y,
                    'z': car.world_position_z,
                },
            })

        # All cars (excluding player, position > 0)
        all_cars_data = []
        for car in state.cars:
            if car.car_index == player_idx:
                continue
            if car.car_position <= 0:
                continue
            all_cars_data.append({
                'carIndex': car.car_index,
                'position': car.car_position,
                'lapDistance': car.lap_distance,
                'lapNumber': car.current_lap_num,
                'world_pos_m': {
                    'x': car.world_position_x,
                    'y': car.world_position_y,
                    'z': car.world_position_z,
                },
            })

        snapshot = {
            'timestamp': int(time.time() * 1000),
            'sessionTime': state.session_time,
            'frameId': state.frame_identifier,
            'meta': meta,
            'player': player_data,
            'nearbyCars': nearby_data,
            'allCars': all_cars_data,
        }

    return json.dumps(snapshot, separators=(',', ':'))


# ─── UDP Receiver ─────────────────────────────────────────────────────────────

def udp_receiver_thread(state, port, stop_event):
    """Background thread: receive UDP packets and update state."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    sock.settimeout(1.0)

    print(f"[f1_receiver] Listening on UDP port {port}...", file=sys.stderr)
    packet_count = 0

    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            process_packet(data, state)
            packet_count += 1
            if packet_count % 1000 == 0:
                print(f"[f1_receiver] {packet_count} packets received", file=sys.stderr)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[f1_receiver] Error: {e}", file=sys.stderr)

    sock.close()


# ─── Output Loop ──────────────────────────────────────────────────────────────

def output_loop(state, stop_event):
    """Output JSON snapshots at configured rate."""
    period = 1.0 / OUTPUT_RATE_HZ
    first_output = True

    while not stop_event.is_set():
        start = time.time()
        snapshot = generate_snapshot(state)
        if snapshot is not None:
            if first_output:
                print(f"[f1_receiver] First output frame!", file=sys.stderr)
                first_output = False
            sys.stdout.write(snapshot + '\n')
            sys.stdout.flush()
        elapsed = time.time() - start
        sleep_time = period - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    port = UDP_PORT

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--port' and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == '--help' or args[i] == '-h':
            print("F1 2025 Telemetry Receiver (Python)")
            print("=" * 40)
            print()
            print("Usage:")
            print("  python3 f1_receiver.py              # Live UDP on port 20777")
            print("  python3 f1_receiver.py --port 20778  # Custom port")
            print()
            print("Output: JSONL to stdout (same format as Java receiver)")
            sys.exit(0)
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    state = SessionState()
    stop_event = threading.Event()

    # Start UDP receiver thread
    recv_thread = threading.Thread(
        target=udp_receiver_thread,
        args=(state, port, stop_event),
        daemon=True,
        name='UDP-Receiver',
    )
    recv_thread.start()

    # Run output loop on main thread
    try:
        output_loop(state, stop_event)
    except KeyboardInterrupt:
        print("\n[f1_receiver] Shutting down...", file=sys.stderr)
    finally:
        stop_event.set()
        recv_thread.join(timeout=2)


if __name__ == '__main__':
    main()
