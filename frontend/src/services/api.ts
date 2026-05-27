export interface PluginInfo {
  id: string
  name: string
  version: string
  description: string
  status: string
  api_version?: string
}

export interface PluginMenu {
  plugin_id: string
  title: string
  icon: string | null
  order: number
  route: string
  frontend_url: string
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data?.detail?.error?.message || data?.error?.message || '请求失败'
    throw new Error(message)
  }
  return data as T
}

export function getPlugins() {
  return request<PluginInfo[]>('/api/admin/plugins')
}

export function getMenus() {
  return request<PluginMenu[]>('/api/runtime/menus')
}

export function uploadPlugin(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request('/api/admin/plugins/upload', { method: 'POST', body: form })
}

export function updatePlugin(id: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  return request(`/api/admin/plugins/${id}/update`, { method: 'POST', body: form })
}

export function enablePlugin(id: string) {
  return request(`/api/admin/plugins/${id}/enable`, { method: 'POST' })
}

export function disablePlugin(id: string) {
  return request(`/api/admin/plugins/${id}/disable`, { method: 'POST' })
}

export function removePlugin(id: string) {
  return request(`/api/admin/plugins/${id}`, { method: 'DELETE' })
}
