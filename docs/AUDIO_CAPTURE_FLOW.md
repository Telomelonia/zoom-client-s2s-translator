# Audio Capture Flow - Phase 2A

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PHYSICAL AUDIO DEVICES                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐              ┌───────────────────────────┐       │
│  │  Microphone      │              │  BlackHole / VB-Audio     │       │
│  │  (Built-in/USB)  │              │  (Virtual Audio Device)   │       │
│  └────────┬─────────┘              └─────────┬─────────────────┘       │
│           │                                   │                         │
└───────────┼───────────────────────────────────┼─────────────────────────┘
            │                                   │
            │ PCM Audio Stream                  │ System Audio (Zoom)
            │ 16kHz, 16-bit, Mono              │ 24kHz, 16-bit, Stereo
            │                                   │
            ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              PyAudio Layer                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐      ┌──────────────────────────┐        │
│  │  PyAudio Stream          │      │  PyAudio Stream          │        │
│  │  (Callback Mode)         │      │  (Callback Mode)         │        │
│  │                          │      │                          │        │
│  │  def callback():         │      │  def callback():         │        │
│  │    - Capture audio       │      │    - Capture audio       │        │
│  │    - Create AudioChunk   │      │    - Stereo→Mono convert │        │
│  │    - Push to queue       │      │    - Create AudioChunk   │        │
│  │                          │      │    - Push to queue       │        │
│  └──────────┬───────────────┘      └──────────┬───────────────┘        │
│             │                                  │                        │
└─────────────┼──────────────────────────────────┼────────────────────────┘
              │                                  │
              │ Runs in separate thread          │ Runs in separate thread
              │ Non-blocking, low latency        │ Non-blocking
              │                                  │
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Capture Classes Layer                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐      ┌──────────────────────────┐        │
│  │  MicrophoneCapture       │      │  SystemAudioCapture      │        │
│  │  extends                 │      │  extends                 │        │
│  │  BaseCaptureDevice       │      │  BaseCaptureDevice       │        │
│  │                          │      │                          │        │
│  │  - asyncio.Queue         │      │  - asyncio.Queue         │        │
│  │  - State: RUNNING        │      │  - State: RUNNING        │        │
│  │  - Stats tracking        │      │  - Stats tracking        │        │
│  │                          │      │  - Numpy conversion      │        │
│  └──────────┬───────────────┘      └──────────┬───────────────┘        │
│             │                                  │                        │
└─────────────┼──────────────────────────────────┼────────────────────────┘
              │                                  │
              │ await read_chunk()               │ await read_chunk()
              │                                  │
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  async def translation_pipeline():                                │  │
│  │                                                                   │  │
│  │      async with MicrophoneCapture() as mic:                      │  │
│  │          while True:                                             │  │
│  │              chunk = await mic.read_chunk()                      │  │
│  │              await send_to_gemini(chunk.data)                    │  │
│  │              translated = await receive_from_gemini()            │  │
│  │              await play_to_speakers(translated)                  │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow - Microphone Capture

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. PyAudio Callback (Separate Thread)                                    │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ in_data: bytes (PCM audio)
                              │ frame_count: int
                              │ timestamp: float
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 2. Create AudioChunk (Immutable)                                         │
│    - data: bytes                                                         │
│    - timestamp: float                                                    │
│    - sample_rate: 16000                                                  │
│    - channels: 1                                                         │
│    - frames: 1024                                                        │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ chunk: AudioChunk
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 3. Push to asyncio.Queue (Non-blocking)                                 │
│    queue.put_nowait(chunk)                                               │
│                                                                          │
│    Queue size: maxsize=100 (~6 seconds buffer)                          │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Thread-safe handoff
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 4. Application reads (Async, Main Thread)                               │
│    chunk = await mic.read_chunk()                                       │
│                                                                          │
│    - Blocks if queue empty (yield to event loop)                        │
│    - Returns immediately if data available                              │
│    - Supports timeout for periodic checks                               │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ chunk.data: bytes
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 5. Send to Gemini S2ST API (Phase 3)                                    │
│    websocket.send_audio(chunk.data)                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow - System Audio Capture (with Stereo Conversion)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. PyAudio Callback (Separate Thread)                                    │
│    in_data: bytes (Stereo PCM: L,R,L,R,L,R...)                          │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ in_data: 4096 bytes (2048 L, 2048 R)
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 2. Convert Stereo to Mono (Numpy)                                       │
│    audio_array = np.frombuffer(in_data, dtype=np.int16)                 │
│    # [L1, R1, L2, R2, L3, R3, ...]                                      │
│                                                                          │
│    audio_array = audio_array.reshape(-1, 2)                             │
│    # [[L1, R1], [L2, R2], [L3, R3], ...]                                │
│                                                                          │
│    mono_array = audio_array.mean(axis=1).astype(np.int16)               │
│    # [(L1+R1)/2, (L2+R2)/2, (L3+R3)/2, ...]                             │
│                                                                          │
│    in_data = mono_array.tobytes()                                       │
│    # 2048 bytes mono                                                    │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              │ in_data: bytes (Mono PCM)
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 3. Create AudioChunk & Queue (same as MicrophoneCapture)                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Device Discovery Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ AudioDeviceManager Initialization                                        │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. Initialize PyAudio                                                    │
│    pyaudio = pyaudio.PyAudio()                                           │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 2. Get Device Count                                                      │
│    device_count = pyaudio.get_device_count()  # e.g., 8                 │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 3. Iterate All Devices                                                   │
│    for i in range(device_count):                                         │
│        info = pyaudio.get_device_info_by_index(i)                        │
│        device = create_device_from_info(i, info)                         │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 4. Classify Each Device                                                  │
│                                                                          │
│    Device Info:                                                          │
│    - name: "BlackHole 2ch"                                               │
│    - maxInputChannels: 2                                                 │
│    - maxOutputChannels: 2                                                │
│    - defaultSampleRate: 48000                                            │
│                                                                          │
│    Classification Logic:                                                 │
│    - Both input/output + "blackhole" in name → LOOPBACK                 │
│    - Only input → INPUT                                                  │
│    - Only output → OUTPUT                                                │
│                                                                          │
│    Result: AudioDevice(                                                  │
│        index=5,                                                          │
│        name="BlackHole 2ch",                                             │
│        device_type=DeviceType.LOOPBACK,                                  │
│        is_virtual_device=True                                            │
│    )                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 5. Store in List                                                         │
│    self._devices.append(device)                                          │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ 6. Expose via Methods                                                    │
│    - get_all_devices()                                                   │
│    - get_input_devices()                                                 │
│    - get_loopback_devices()                                              │
│    - find_blackhole_device()                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Application Code                                                          │
│                                                                          │
│ async with MicrophoneCapture() as mic:                                  │
│     chunk = await mic.read_chunk()                                      │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
          ┌──────────────────┐  ┌──────────────────┐
          │  Success Path    │  │  Error Path      │
          └──────────────────┘  └──────────────────┘
                    │                   │
                    │                   │
                    ▼                   ▼
          ┌──────────────────┐  ┌──────────────────────────────────┐
          │ Return chunk     │  │ Exception Raised:                │
          │ data: bytes      │  │ - AudioDeviceError               │
          └──────────────────┘  │   → Device not found/unavailable │
                                │ - AudioStreamError               │
                                │   → Stream failure               │
                                │ - asyncio.TimeoutError           │
                                │   → No data in timeout period    │
                                └──────────────────────────────────┘
                                            │
                                            ▼
                                ┌──────────────────────────────────┐
                                │ Automatic Cleanup:               │
                                │ - Stop PyAudio stream            │
                                │ - Close resources                │
                                │ - Set state to STOPPED/ERROR     │
                                │ - Log error details              │
                                └──────────────────────────────────┘
```

---

## State Machine

```
┌─────────┐
│ STOPPED │  ← Initial state
└────┬────┘
     │
     │ await start()
     ▼
┌──────────┐
│ STARTING │  ← Initializing PyAudio
└────┬─────┘
     │
     │ Success
     ▼
┌─────────┐
│ RUNNING │  ← Actively capturing audio
└────┬────┘
     │
     │ await stop() or Error
     ▼
┌──────────┐
│ STOPPING │  ← Cleaning up resources
└────┬─────┘
     │
     ├──► Success ──────┐
     │                  ▼
     │             ┌─────────┐
     │             │ STOPPED │
     │             └─────────┘
     │
     └──► Error ───────┐
                       ▼
                  ┌───────┐
                  │ ERROR │
                  └───────┘
```

---

## Memory Management

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Audio Capture Memory Usage                                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PyAudio Stream Buffers                         ~100 KB                 │
│  ├─ Internal PortAudio buffers                                          │
│  └─ System audio driver buffers                                         │
│                                                                          │
│  asyncio.Queue (maxsize=100)                    ~2 MB                   │
│  ├─ 100 AudioChunk objects                                              │
│  ├─ Each chunk: ~2048 bytes audio data                                  │
│  └─ Metadata: ~100 bytes per chunk                                      │
│                                                                          │
│  Numpy Conversion Buffer (SystemAudioCapture)   ~4 KB                   │
│  └─ Temporary array for stereo→mono                                     │
│                                                                          │
│  Total per capture instance:                    ~2.1 MB                 │
│                                                                          │
│  Both captures (Mic + System):                  ~4.2 MB                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Latency Breakdown (MicrophoneCapture)                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Microphone → PyAudio                           ~5-10 ms                │
│  (Hardware latency)                                                      │
│                                                                          │
│  PyAudio Callback → Queue                       ~1 ms                   │
│  (Thread context switch + put_nowait)                                   │
│                                                                          │
│  Queue → Application                            ~1 ms                   │
│  (Event loop scheduling)                                                │
│                                                                          │
│  Chunk Duration (1024 @ 16kHz)                  ~64 ms                  │
│                                                                          │
│  Total End-to-End Latency:                      ~70-75 ms               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ CPU Usage (Single Core)                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PyAudio Callback (idle)                        <0.5%                   │
│  PyAudio Callback (active)                      1-2%                    │
│  Stereo→Mono Conversion (numpy)                 0.5-1%                  │
│  Queue Management                               <0.5%                   │
│  Application Processing                         Depends on use          │
│                                                                          │
│  Total (Mic only):                              1-2%                    │
│  Total (Mic + System):                          2-5%                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

This comprehensive flow diagram shows how all components work together in Phase 2A!
