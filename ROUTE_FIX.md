# 异常用户页面路由修复

## 问题描述
异常客户右上角的"查看全部"按钮点击后提示404错误，这是因为路由没有配置异常用户页面的路径。

## 解决方案

### 1. 添加路由配置
在 `frontend/src/router/index.js` 中添加了异常用户页面的路由：

```javascript
{ 
  path: 'abnormal-users', 
  name: 'AdminAbnormalUsers', 
  component: () => import('@/views/admin/AbnormalUsers.vue'), 
  meta: { 
    title: '异常用户监控', 
    breadcrumb: [
      { title: '管理后台', path: '/admin/dashboard' }, 
      { title: '异常用户监控', path: '/admin/abnormal-users' }
    ] 
  } 
}
```

### 2. 添加侧边栏导航
在 `frontend/src/components/layout/AdminLayout.vue` 中添加了异常用户监控的菜单项：

```vue
<router-link 
  to="/admin/abnormal-users"
  class="nav-item"
  :class="{ active: $route.path === '/admin/abnormal-users' }"
>
  <i class="el-icon-warning"></i>
  <span class="nav-text" v-show="!sidebarCollapsed">异常用户监控</span>
</router-link>
```

## 路由信息

### 页面路径
- **URL**: `/admin/abnormal-users`
- **组件**: `AbnormalUsers.vue`
- **权限**: 需要管理员权限

### 面包屑导航
- 管理后台 > 异常用户监控

### 侧边栏位置
- 在"用户管理"分组下
- 位于"用户列表"和"订阅管理"之间
- 使用警告图标 `el-icon-warning`

## 功能特性

### 异常用户监控页面包含：
1. **统计卡片**：显示异常用户总数、频繁重置用户、频繁订阅用户、多重异常用户
2. **异常用户列表**：显示用户名、邮箱、异常类型、异常次数、最后活动时间
3. **用户详情查看**：点击用户名或邮箱可查看详细信息
4. **监控设置**：可以调整异常检测的阈值
5. **标记正常**：可以将异常用户标记为正常状态

### 异常检测规则：
- **频繁重置**：30天内重置订阅超过5次
- **频繁订阅**：30天内创建超过3个订阅
- **多重异常**：同时满足上述两个条件

## 测试验证

### 访问方式：
1. 从仪表盘点击"查看全部"按钮
2. 从侧边栏点击"异常用户监控"菜单
3. 直接访问URL：`/admin/abnormal-users`

### 预期结果：
- 页面正常加载，不再出现404错误
- 显示异常用户监控界面
- 侧边栏菜单项高亮显示
- 面包屑导航正确显示

## 文件修改清单

### 修改的文件：
1. `frontend/src/router/index.js` - 添加路由配置
2. `frontend/src/components/layout/AdminLayout.vue` - 添加侧边栏菜单

### 相关文件：
1. `frontend/src/views/admin/AbnormalUsers.vue` - 异常用户监控页面（已存在）
2. `frontend/src/views/admin/Dashboard.vue` - 仪表盘页面（包含跳转按钮）

## 注意事项

1. 确保异常用户监控页面组件存在且正常工作
2. 确保API端点 `/admin/users/abnormal` 正常返回数据
3. 确保用户有管理员权限才能访问此页面
4. 路由配置需要在开发服务器重启后生效

## 后续优化建议

1. 添加异常用户的实时监控功能
2. 添加异常用户自动告警功能
3. 优化异常检测算法
4. 添加更多异常行为类型
5. 添加数据导出功能
