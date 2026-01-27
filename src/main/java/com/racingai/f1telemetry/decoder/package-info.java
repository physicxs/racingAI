/**
 * Binary packet decoding and validation.
 *
 * Handles:
 * - UDP packet reception
 * - Endianness detection
 * - Binary-to-object decoding
 * - Packet validation and sanity checks
 * - Known spec issue workarounds (e.g., LapData field swap)
 */
package com.racingai.f1telemetry.decoder;
