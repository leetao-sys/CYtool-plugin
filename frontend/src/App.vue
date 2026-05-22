<template>
  <el-container class="app-shell">
    <el-aside width="260px" class="sidebar">
      <h2>CYtool</h2>
      <el-menu :default-active="active" @select="active = $event">
        <el-menu-item index="manage">插件管理</el-menu-item>
        <el-menu-item
          v-for="item in menus"
          :key="item.plugin_id"
          :index="item.plugin_id"
        >
          {{ item.title }}
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <PluginManager v-if="active === 'manage'" @changed="refresh" />
      <iframe
        v-else
        class="plugin-frame"
        :src="currentPlugin?.frontend_url"
        title="plugin"
      />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PluginManager from './components/PluginManager.vue'
import { getMenus, type PluginMenu } from './services/api'

const active = ref('manage')
const menus = ref<PluginMenu[]>([])
const currentPlugin = computed(() => menus.value.find(item => item.plugin_id === active.value))

async function refresh() {
  menus.value = await getMenus()
  if (active.value !== 'manage' && !currentPlugin.value) active.value = 'manage'
}

onMounted(refresh)
</script>
