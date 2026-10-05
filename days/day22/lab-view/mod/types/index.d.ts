export type Item = { title: string; owner: string; waiting: string; today: string; next: string; ids: string[] }
export type HookEvent = { action: string; items?: string[] }
export type Result = { sender: string; receiver: string; gate: string }
export type Snapshot = { source: string; items: Item[]; blocks: HookEvent[]; results: Record<string, Result>; checkedAt: number; error?: string }

declare module 'claude-code' {
  interface PluginState {
    'work-view': { snapshot: Snapshot }
  }
}
