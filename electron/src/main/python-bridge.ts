// electron/src/main/python-bridge.ts

import { ChildProcess, spawn } from 'child_process';
import { EventEmitter } from 'events';
import { join } from 'path';
import type { PythonCommand, PythonMessage } from '../shared/types.js';

/**
 * Manages the Python subprocess and JSON-line IPC.
 */
export class PythonBridge extends EventEmitter {
  private proc: ChildProcess | null = null;
  private buffer = '';
  private stopping = false;

  /** Spawn the Python server and wait for the "ready" event. */
  async start(): Promise<void> {
    if (this.proc) return;

    // __dirname is electron/dist/main/ — go up 3 levels to project root
    const projectRoot = join(__dirname, '..', '..', '..');
    const serverPath = join(projectRoot, 'python', 'server.py');

    this.proc = spawn('python3', [serverPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: projectRoot,
    });

    this.stopping = false;

    this.proc.stdout!.on('data', (chunk: Buffer) => {
      this.buffer += chunk.toString();
      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const msg: PythonMessage = JSON.parse(line);
          this.emit('message', msg);
        } catch {
          console.error('[python-bridge] bad JSON:', line);
        }
      }
    });

    this.proc.stderr!.on('data', (chunk: Buffer) => {
      console.log('[python]', chunk.toString().trimEnd());
    });

    this.proc.once('exit', (code) => {
      console.log(`[python-bridge] exited with code ${code}`);
      this.proc = null;
      this.emit('exit', code);
    });

    await this.waitFor('ready', 10_000);
  }

  /** Send a JSON command to the Python process. */
  send(cmd: PythonCommand): void {
    if (!this.proc?.stdin?.writable) {
      throw new Error('Python process not running');
    }
    this.proc.stdin.write(JSON.stringify(cmd) + '\n');
  }

  /** Send a command and wait for a specific response type. */
  async sendAndWait<T extends PythonMessage['type']>(
    cmd: PythonCommand,
    responseType: T,
    timeoutMs = 10_000,
  ): Promise<Extract<PythonMessage, { type: T }>> {
    this.send(cmd);
    return this.waitFor(responseType, timeoutMs);
  }

  /** Wait for a specific message type. Rejects immediately on error messages. */
  private waitFor<T extends PythonMessage['type']>(
    messageType: T,
    timeoutMs: number,
  ): Promise<Extract<PythonMessage, { type: T }>> {
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        clearTimeout(timer);
        this.removeListener('message', handler);
      };

      const timer = setTimeout(() => {
        cleanup();
        reject(new Error(`Timeout waiting for "${messageType}" (${timeoutMs}ms)`));
      }, timeoutMs);

      const handler = (msg: PythonMessage) => {
        if (msg.type === messageType) {
          cleanup();
          resolve(msg as Extract<PythonMessage, { type: T }>);
        } else if (msg.type === 'error' && messageType !== 'error') {
          cleanup();
          reject(new Error((msg as { type: 'error'; message: string }).message));
        }
      };

      this.on('message', handler);
    });
  }

  /** Gracefully stop the Python process. */
  async stop(): Promise<void> {
    if (!this.proc || this.stopping) return;
    this.stopping = true;

    try {
      this.send({ cmd: 'stop' });
    } catch {
      // stdin may already be closed
    }

    this.proc.stdin?.end();

    await new Promise<void>((resolve) => {
      const timer = setTimeout(() => {
        this.proc?.kill('SIGKILL');
        resolve();
      }, 3_000);

      if (this.proc) {
        this.proc.once('exit', () => {
          clearTimeout(timer);
          resolve();
        });
      } else {
        clearTimeout(timer);
        resolve();
      }
    });

    this.proc = null;
    this.stopping = false;
  }

  get isRunning(): boolean {
    return this.proc !== null && !this.stopping;
  }
}
