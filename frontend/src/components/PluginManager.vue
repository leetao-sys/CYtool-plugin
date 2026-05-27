<template>
  <section class="manager-page">
    <div class="hero-panel">
      <div>
        <p class="eyebrow">Plugin Center</p>
        <h1>插件管理</h1>
        <p class="hero-copy">安装、更新、启用、禁用和卸载工具插件。插件以 zip 包发布，安装后会自动出现在左侧菜单。</p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" size="large" :loading="uploading" @click="openInstallPicker">
          安装插件
        </el-button>
        <el-button size="large" @click="refresh">刷新</el-button>
        <input ref="installInput" class="hidden-input" type="file" accept=".zip" @change="installFromInput" />
        <input ref="updateInput" class="hidden-input" type="file" accept=".zip" @change="updateFromInput" />
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <span>插件总数</span>
        <strong>{{ plugins.length }}</strong>
      </div>
      <div class="stat-card">
        <span>已启用</span>
        <strong>{{ enabledCount }}</strong>
      </div>
      <div class="stat-card">
        <span>已禁用</span>
        <strong>{{ disabledCount }}</strong>
      </div>
      <div class="stat-card">
        <span>最新刷新</span>
        <strong>{{ lastRefreshText }}</strong>
      </div>
    </div>

    <section class="table-panel">
      <div class="table-header">
        <div>
          <h2>插件列表</h2>
          <p>更新插件时请选择相同插件 ID 的 zip 包，平台会自动校验 ID 是否匹配。</p>
        </div>
        <el-input v-model="keyword" class="search-input" placeholder="搜索插件名称、ID 或描述" clearable />
      </div>

      <el-table v-loading="loading" :data="filteredPlugins" class="plugin-table" empty-text="暂无插件，请先安装 zip 包">
        <el-table-column label="插件" min-width="240">
          <template #default="{ row }">
            <div class="plugin-name-cell">
              <div class="plugin-avatar">{{ initials(row.name) }}</div>
              <div>
                <strong>{{ row.name }}</strong>
                <small>{{ row.id }}</small>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="110" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" effect="light">
              {{ row.status === 'enabled' ? '已启用' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip />
        <el-table-column label="操作" width="310" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="toggle(row)">
              {{ row.status === 'enabled' ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="primary" plain @click="openUpdatePicker(row)">更新</el-button>
            <el-button size="small" type="danger" plain @click="remove(row)">卸载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  disablePlugin,
  enablePlugin,
  getPlugins,
  removePlugin,
  updatePlugin,
  uploadPlugin,
  type PluginInfo
} from '../services/api'

const emit = defineEmits<{ changed: [] }>()
const plugins = ref<PluginInfo[]>([])
const loading = ref(false)
const uploading = ref(false)
const keyword = ref('')
const lastRefresh = ref<Date | null>(null)
const installInput = ref<HTMLInputElement>()
const updateInput = ref<HTMLInputElement>()
const updateTarget = ref<PluginInfo | null>(null)

const enabledCount = computed(() => plugins.value.filter(item => item.status === 'enabled').length)
const disabledCount = computed(() => plugins.value.filter(item => item.status !== 'enabled').length)
const lastRefreshText = computed(() => lastRefresh.value ? lastRefresh.value.toLocaleTimeString() : '-')
const filteredPlugins = computed(() => {
  const value = keyword.value.trim().toLowerCase()
  if (!value) return plugins.value
  return plugins.value.filter(plugin =>
    [plugin.name, plugin.id, plugin.description, plugin.version]
      .some(field => field?.toLowerCase().includes(value))
  )
})

async function refresh() {
  loading.value = true
  try {
    plugins.value = await getPlugins()
    lastRefresh.value = new Date()
    emit('changed')
  } finally {
    loading.value = false
  }
}

function openInstallPicker() {
  installInput.value?.click()
}

function openUpdatePicker(plugin: PluginInfo) {
  updateTarget.value = plugin
  updateInput.value?.click()
}

async function installFromInput(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    uploading.value = true
    await uploadPlugin(file)
    ElMessage.success('插件安装成功')
    await refresh()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '插件安装失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function updateFromInput(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const target = updateTarget.value
  if (!file || !target) return
  try {
    uploading.value = true
    await updatePlugin(target.id, file)
    ElMessage.success(`${target.name} 更新成功`)
    await refresh()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '插件更新失败')
  } finally {
    uploading.value = false
    updateTarget.value = null
    input.value = ''
  }
}

async function toggle(plugin: PluginInfo) {
  try {
    if (plugin.status === 'enabled') {
      await disablePlugin(plugin.id)
      ElMessage.success('插件已禁用')
    } else {
      await enablePlugin(plugin.id)
      ElMessage.success('插件已启用')
    }
    await refresh()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '操作失败')
  }
}

async function remove(plugin: PluginInfo) {
  try {
    await ElMessageBox.confirm(`确认卸载插件「${plugin.name}」吗？`, '卸载确认', {
      type: 'warning',
      confirmButtonText: '卸载',
      cancelButtonText: '取消'
    })
    await removePlugin(plugin.id)
    ElMessage.success('插件已卸载')
    await refresh()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error instanceof Error ? error.message : '卸载失败')
  }
}

function initials(name: string) {
  return name
    .split(/\s|-/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('') || 'PL'
}

onMounted(refresh)
</script>
