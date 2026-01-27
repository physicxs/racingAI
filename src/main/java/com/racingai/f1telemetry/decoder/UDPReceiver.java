package com.racingai.f1telemetry.decoder;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * UDP receiver for F1 2025 telemetry packets.
 *
 * Listens on port 20777 for incoming UDP packets from the F1 25 game.
 * Runs in a separate thread and notifies listeners when packets arrive.
 *
 * Thread-safe and supports graceful shutdown.
 */
public class UDPReceiver implements Runnable {

    private static final Logger logger = LoggerFactory.getLogger(UDPReceiver.class);

    private static final int MAX_PACKET_SIZE = 2048; // F1 packets are typically < 1500 bytes
    private static final int SOCKET_TIMEOUT_MS = 1000; // Check shutdown flag every second

    private final int port;
    private final List<PacketListener> listeners;
    private final AtomicBoolean running;

    private DatagramSocket socket;
    private Thread receiverThread;

    /**
     * Creates a UDP receiver for the specified port.
     *
     * @param port UDP port to listen on (default: 20777)
     */
    public UDPReceiver(int port) {
        this.port = port;
        this.listeners = new ArrayList<>();
        this.running = new AtomicBoolean(false);
    }

    /**
     * Adds a packet listener.
     *
     * @param listener Listener to receive packet callbacks
     */
    public void addListener(PacketListener listener) {
        synchronized (listeners) {
            listeners.add(listener);
        }
    }

    /**
     * Removes a packet listener.
     *
     * @param listener Listener to remove
     */
    public void removeListener(PacketListener listener) {
        synchronized (listeners) {
            listeners.remove(listener);
        }
    }

    /**
     * Starts the UDP receiver in a new thread.
     *
     * @throws IOException if the socket cannot be opened
     */
    public void start() throws IOException {
        if (running.get()) {
            logger.warn("UDP receiver already running");
            return;
        }

        logger.info("Starting UDP receiver on port {}", port);

        // Create and bind socket
        try {
            socket = new DatagramSocket(port);
            socket.setSoTimeout(SOCKET_TIMEOUT_MS);
            logger.info("UDP socket bound to port {}", port);
        } catch (SocketException e) {
            logger.error("Failed to bind UDP socket to port {}: {}", port, e.getMessage());
            throw new IOException("Failed to bind UDP socket", e);
        }

        // Start receiver thread
        running.set(true);
        receiverThread = new Thread(this, "UDP-Receiver-" + port);
        receiverThread.setDaemon(false);
        receiverThread.start();

        logger.info("UDP receiver started successfully");
    }

    /**
     * Stops the UDP receiver and closes the socket.
     */
    public void stop() {
        if (!running.get()) {
            return;
        }

        logger.info("Stopping UDP receiver...");
        running.set(false);

        // Close socket to unblock receive
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }

        // Wait for thread to finish
        if (receiverThread != null && receiverThread.isAlive()) {
            try {
                receiverThread.join(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.warn("Interrupted while waiting for receiver thread to stop");
            }
        }

        logger.info("UDP receiver stopped");
    }

    /**
     * Main receiver loop (runs in separate thread).
     */
    @Override
    public void run() {
        logger.info("UDP receiver thread started");
        byte[] buffer = new byte[MAX_PACKET_SIZE];
        DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

        long packetsReceived = 0;
        long lastLogTime = System.currentTimeMillis();

        while (running.get()) {
            try {
                // Receive packet (blocks until timeout or packet arrives)
                socket.receive(packet);

                packetsReceived++;

                // Notify listeners with a copy of the data
                byte[] data = new byte[packet.getLength()];
                System.arraycopy(packet.getData(), packet.getOffset(), data, 0, packet.getLength());

                notifyListeners(data, packet.getLength());

                // Log statistics every 5 seconds
                long now = System.currentTimeMillis();
                if (now - lastLogTime >= 5000) {
                    logger.debug("UDP receiver: {} packets received", packetsReceived);
                    lastLogTime = now;
                }

            } catch (SocketTimeoutException e) {
                // Normal timeout - check if we should continue running
                continue;
            } catch (IOException e) {
                if (running.get()) {
                    logger.error("Error receiving UDP packet: {}", e.getMessage());
                    notifyError(e);
                }
            }
        }

        logger.info("UDP receiver thread stopped. Total packets received: {}", packetsReceived);
    }

    /**
     * Notifies all listeners of a received packet.
     */
    private void notifyListeners(byte[] data, int length) {
        List<PacketListener> listenersCopy;
        synchronized (listeners) {
            listenersCopy = new ArrayList<>(listeners);
        }

        for (PacketListener listener : listenersCopy) {
            try {
                listener.onPacketReceived(data, length);
            } catch (Exception e) {
                logger.error("Error in packet listener: {}", e.getMessage(), e);
            }
        }
    }

    /**
     * Notifies all listeners of an error.
     */
    private void notifyError(Exception error) {
        List<PacketListener> listenersCopy;
        synchronized (listeners) {
            listenersCopy = new ArrayList<>(listeners);
        }

        for (PacketListener listener : listenersCopy) {
            try {
                listener.onError(error);
            } catch (Exception e) {
                logger.error("Error in error handler: {}", e.getMessage(), e);
            }
        }
    }

    /**
     * Checks if the receiver is currently running.
     */
    public boolean isRunning() {
        return running.get();
    }

    /**
     * Gets the port this receiver is listening on.
     */
    public int getPort() {
        return port;
    }
}
