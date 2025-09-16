<template>
  <div class="help-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>帮助文档</h1>
      <p>使用指南和常见问题解答</p>
    </div>

    <div class="help-content">
      <!-- 快速导航 -->
      <el-card class="nav-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-menu"></i>
            快速导航
          </div>
        </template>
        
        <div class="nav-links">
          <el-button 
            v-for="section in sections" 
            :key="section.id"
            type="primary" 
            plain
            @click="scrollToSection(section.id)"
          >
            {{ section.title }}
          </el-button>
        </div>
      </el-card>

      <!-- 使用指南 -->
      <el-card class="guide-card" id="guide">
        <template #header>
          <div class="card-header">
            <i class="el-icon-guide"></i>
            使用指南
          </div>
        </template>

        <el-collapse v-model="activeNames">
          <el-collapse-item 
            v-for="guide in guides" 
            :key="guide.id"
            :title="guide.title"
            :name="guide.id"
          >
            <div class="guide-content" v-html="guide.content"></div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 常见问题 -->
      <el-card class="faq-card" id="faq">
        <template #header>
          <div class="card-header">
            <i class="el-icon-question"></i>
            常见问题
          </div>
        </template>

        <el-collapse v-model="activeFAQ">
          <el-collapse-item 
            v-for="faq in faqs" 
            :key="faq.id"
            :title="faq.question"
            :name="faq.id"
          >
            <div class="faq-content" v-html="faq.answer"></div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <!-- 客户端下载 -->
      <el-card class="clients-card" id="clients">
        <template #header>
          <div class="card-header">
            <i class="el-icon-download"></i>
            客户端下载
          </div>
        </template>

        <div class="clients-grid">
          <div 
            v-for="client in clients" 
            :key="client.id"
            class="client-item"
          >
            <div class="client-icon">
              <i :class="client.icon"></i>
            </div>
            <div class="client-info">
              <h4>{{ client.name }}</h4>
              <p>{{ client.description }}</p>
              <div class="client-platforms">
                <el-tag 
                  v-for="platform in client.platforms" 
                  :key="platform"
                  size="small"
                  style="margin-right: 5px;"
                >
                  {{ platform }}
                </el-tag>
              </div>
            </div>
            <div class="client-actions">
              <el-button 
                type="primary" 
                size="small"
                @click="downloadClient(client.downloadUrl)"
              >
                下载
              </el-button>
              <el-button 
                type="info" 
                size="small"
                @click="viewClientGuide(client.guideUrl)"
              >
                教程
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 联系我们 -->
      <el-card class="contact-card" id="contact">
        <template #header>
          <div class="card-header">
            <i class="el-icon-service"></i>
            联系我们
          </div>
        </template>

        <div class="contact-info">
          <div class="contact-item">
            <i class="el-icon-message"></i>
            <div class="contact-details">
              <h4>邮箱验证</h4>
              <p>support@yourdomain.com</p>
            </div>
          </div>
          
          <div class="contact-item">
            <i class="el-icon-chat-dot-round"></i>
            <div class="contact-details">
              <h4>QQ群</h4>
              <p>请通过邮箱联系我们</p>
            </div>
          </div>
          
          <div class="contact-item">
            <i class="el-icon-time"></i>
            <div class="contact-details">
              <h4>服务时间</h4>
              <p>周一至周日 9:00-22:00</p>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'Help',
  setup() {
    const activeNames = ref(['guide-1'])
    const activeFAQ = ref(['faq-1'])

    const sections = [
      { id: 'guide', title: '使用指南' },
      { id: 'faq', title: '常见问题' },
      { id: 'clients', title: '客户端下载' },
      { id: 'contact', title: '联系我们' }
    ]

    const guides = [
      {
        id: 'guide-1',
        title: '如何注册账户？',
        content: `
          <ol>
            <li>点击页面右上角的"注册"按钮</li>
            <li>输入您的邮箱地址</li>
            <li>设置密码（不少于6位）</li>
            <li>点击"注册"按钮</li>
            <li>查收邮箱验证邮件并点击验证链接</li>
            <li>验证成功后即可登录使用</li>
          </ol>
        `
      },
      {
        id: 'guide-2',
        title: '如何购买套餐？',
        content: `
          <ol>
            <li>登录后点击"套餐订阅"</li>
            <li>选择合适的套餐</li>
            <li>选择支付方式（支付宝/微信）</li>
            <li>扫码完成支付</li>
            <li>支付成功后自动开通服务</li>
          </ol>
        `
      },
      {
        id: 'guide-3',
        title: '如何配置客户端？',
        content: `
          <ol>
            <li>在仪表板页面复制订阅地址</li>
            <li>打开客户端软件</li>
            <li>选择"从URL导入"或"订阅"</li>
            <li>粘贴订阅地址并确认</li>
            <li>等待配置下载完成</li>
            <li>选择节点并连接</li>
          </ol>
        `
      },
      {
        id: 'guide-4',
        title: '如何重置订阅地址？',
        content: `
          <ol>
            <li>当设备数量达到上限时，可以重置订阅地址</li>
            <li>在仪表板页面点击"一键重置订阅地址"</li>
            <li>确认重置操作</li>
            <li>使用新的订阅地址重新配置所有设备</li>
            <li>注意：重置后旧地址将失效</li>
          </ol>
        `
      }
    ]

    const faqs = [
      {
        id: 'faq-1',
        question: '为什么我的订阅无法使用？',
        answer: `
          <p>可能的原因：</p>
          <ul>
            <li>订阅已过期，请续费</li>
            <li>设备数量超限，请重置订阅地址</li>
            <li>网络连接问题，请检查网络</li>
            <li>客户端配置错误，请重新配置</li>
          </ul>
        `
      },
      {
        id: 'faq-2',
        question: '如何查看我的设备列表？',
        answer: `
          <p>登录后点击"设备管理"页面，可以查看：</p>
          <ul>
            <li>当前在线设备</li>
            <li>设备类型和IP地址</li>
            <li>最后访问时间</li>
            <li>移除不需要的设备</li>
          </ul>
        `
      },
      {
        id: 'faq-3',
        question: '支持哪些客户端软件？',
        answer: `
          <p>我们支持以下客户端：</p>
          <ul>
            <li><strong>iOS:</strong> Shadowrocket、Quantumult X、Surge</li>
            <li><strong>Android:</strong> Clash Meta、V2RayNG、SagerNet</li>
            <li><strong>Windows:</strong> Clash for Windows、V2RayN</li>
            <li><strong>Mac:</strong> ClashX Pro、V2RayX</li>
          </ul>
        `
      },
      {
        id: 'faq-4',
        question: '如何修改密码？',
        answer: `
          <p>修改密码步骤：</p>
          <ol>
            <li>登录后点击"个人资料"</li>
            <li>在"修改密码"区域输入当前密码</li>
            <li>输入新密码（不少于6位）</li>
            <li>确认新密码</li>
            <li>点击"修改密码"按钮</li>
          </ol>
        `
      },
      {
        id: 'faq-5',
        question: '忘记密码怎么办？',
        answer: `
          <p>忘记密码可以通过以下方式找回：</p>
          <ol>
            <li>在登录页面点击"忘记密码？"</li>
            <li>输入您的邮箱地址</li>
            <li>查收重置密码邮件</li>
            <li>点击邮件中的重置链接</li>
            <li>设置新密码</li>
          </ol>
        `
      }
    ]

    const clients = [
      {
        id: 1,
        name: 'Clash for Windows',
        description: 'Windows平台最受欢迎的代理客户端',
        icon: 'el-icon-monitor',
        platforms: ['Windows'],
        downloadUrl: 'https://github.com/Fndroid/clash_for_windows_pkg/releases',
        guideUrl: '#'
      },
      {
        id: 2,
        name: 'Clash Meta for Android',
        description: 'Android平台功能强大的代理客户端',
        icon: 'el-icon-mobile-phone',
        platforms: ['Android'],
        downloadUrl: 'https://github.com/MetaCubeX/ClashMetaForAndroid/releases',
        guideUrl: '#'
      },
      {
        id: 3,
        name: 'Shadowrocket',
        description: 'iOS平台优秀的代理客户端',
        icon: 'el-icon-iphone',
        platforms: ['iOS'],
        downloadUrl: 'https://apps.apple.com/app/shadowrocket/id932747118',
        guideUrl: '#'
      },
      {
        id: 4,
        name: 'V2RayN',
        description: 'Windows平台轻量级代理客户端',
        icon: 'el-icon-monitor',
        platforms: ['Windows'],
        downloadUrl: 'https://github.com/2dust/v2rayN/releases',
        guideUrl: '#'
      }
    ]

    // 滚动到指定区域
    const scrollToSection = (sectionId) => {
      const element = document.getElementById(sectionId)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }

    // 下载客户端
    const downloadClient = (url) => {
      window.open(url, '_blank')
    }

    // 查看客户端教程
    const viewClientGuide = (url) => {
      window.open(url, '_blank')
    }

    return {
      activeNames,
      activeFAQ,
      sections,
      guides,
      faqs,
      clients,
      scrollToSection,
      downloadClient,
      viewClientGuide
    }
  }
}
</script>

<style scoped>
.help-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h1 {
  color: #1677ff;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
  font-size: 1rem;
}

.help-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.nav-card,
.guide-card,
.faq-card,
.clients-card,
.contact-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.guide-content,
.faq-content {
  line-height: 1.6;
  color: #333;
}

.guide-content ol,
.faq-content ol {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

.guide-content ul,
.faq-content ul {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

.guide-content li,
.faq-content li {
  margin-bottom: 0.5rem;
}

.clients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.client-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.client-item:hover {
  background: #e3f2fd;
  transform: translateY(-2px);
}

.client-icon {
  font-size: 2rem;
  color: #1677ff;
  width: 60px;
  text-align: center;
}

.client-info {
  flex: 1;
}

.client-info h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-weight: 600;
}

.client-info p {
  margin: 0 0 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
}

.client-platforms {
  margin-top: 0.5rem;
}

.client-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.contact-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.contact-item i {
  font-size: 2rem;
  color: #1677ff;
  width: 50px;
  text-align: center;
}

.contact-details h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-weight: 600;
}

.contact-details p {
  margin: 0;
  color: #666;
}

@media (max-width: 768px) {
  .help-container {
    padding: 10px;
  }
  
  .nav-links {
    flex-direction: column;
  }
  
  .clients-grid {
    grid-template-columns: 1fr;
  }
  
  .client-item {
    flex-direction: column;
    text-align: center;
  }
  
  .client-actions {
    flex-direction: row;
    justify-content: center;
  }
  
  .contact-info {
    grid-template-columns: 1fr;
  }
}
</style> 