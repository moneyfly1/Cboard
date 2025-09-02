import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

// 配置dayjs
dayjs.locale('zh-cn')
dayjs.extend(relativeTime)
dayjs.extend(utc)
dayjs.extend(timezone)

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期
 * @param {string} format - 格式字符串
 * @returns {string} 格式化后的日期字符串
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''
  return dayjs(date).format(format)
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式字符串
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  return dayjs(date).format(format)
}

/**
 * 格式化时间
 * @param {string|Date} date - 日期
 * @param {string} format - 格式字符串
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(date, format = 'HH:mm:ss') {
  if (!date) return ''
  return dayjs(date).format(format)
}

/**
 * 获取相对时间
 * @param {string|Date} date - 日期
 * @returns {string} 相对时间字符串
 */
export function getRelativeTime(date) {
  if (!date) return ''
  return dayjs(date).fromNow()
}

/**
 * 获取时间差
 * @param {string|Date} date1 - 日期1
 * @param {string|Date} date2 - 日期2
 * @param {string} unit - 单位 (day, hour, minute, second)
 * @returns {number} 时间差
 */
export function getTimeDiff(date1, date2, unit = 'day') {
  return dayjs(date1).diff(dayjs(date2), unit)
}

/**
 * 检查日期是否过期
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否过期
 */
export function isExpired(date) {
  if (!date) return true
  return dayjs(date).isBefore(dayjs())
}

/**
 * 检查日期是否即将过期（7天内）
 * @param {string|Date} date - 日期
 * @param {number} days - 天数阈值
 * @returns {boolean} 是否即将过期
 */
export function isExpiringSoon(date, days = 7) {
  if (!date) return false
  const expiryDate = dayjs(date)
  const now = dayjs()
  const diffDays = expiryDate.diff(now, 'day')
  return diffDays >= 0 && diffDays <= days
}

/**
 * 获取剩余天数
 * @param {string|Date} date - 日期
 * @returns {number} 剩余天数
 */
export function getRemainingDays(date) {
  if (!date) return 0
  const expiryDate = dayjs(date)
  const now = dayjs()
  const diffDays = expiryDate.diff(now, 'day')
  return Math.max(0, diffDays)
}

/**
 * 获取剩余时间
 * @param {string|Date} date - 日期
 * @returns {object} 剩余时间对象
 */
export function getRemainingTime(date) {
  if (!date) return { days: 0, hours: 0, minutes: 0, seconds: 0 }
  
  const expiryDate = dayjs(date)
  const now = dayjs()
  const diff = expiryDate.diff(now)
  
  if (diff <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 }
  }
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)
  
  return { days, hours, minutes, seconds }
}

/**
 * 格式化剩余时间
 * @param {string|Date} date - 日期
 * @returns {string} 格式化的剩余时间字符串
 */
export function formatRemainingTime(date) {
  if (!date) return '已过期'
  
  const remaining = getRemainingTime(date)
  
  if (remaining.days > 0) {
    return `${remaining.days}天${remaining.hours}小时`
  } else if (remaining.hours > 0) {
    return `${remaining.hours}小时${remaining.minutes}分钟`
  } else if (remaining.minutes > 0) {
    return `${remaining.minutes}分钟${remaining.seconds}秒`
  } else if (remaining.seconds > 0) {
    return `${remaining.seconds}秒`
  } else {
    return '已过期'
  }
}

/**
 * 获取月份名称
 * @param {number} month - 月份 (1-12)
 * @returns {string} 月份名称
 */
export function getMonthName(month) {
  const monthNames = [
    '一月', '二月', '三月', '四月', '五月', '六月',
    '七月', '八月', '九月', '十月', '十一月', '十二月'
  ]
  return monthNames[month - 1] || ''
}

/**
 * 获取星期名称
 * @param {number} day - 星期 (0-6, 0为星期日)
 * @returns {string} 星期名称
 */
export function getWeekdayName(day) {
  const weekdayNames = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return weekdayNames[day] || ''
}

/**
 * 检查是否为今天
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否为今天
 */
export function isToday(date) {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'day')
}

/**
 * 检查是否为昨天
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否为昨天
 */
export function isYesterday(date) {
  if (!date) return false
  return dayjs(date).isSame(dayjs().subtract(1, 'day'), 'day')
}

/**
 * 检查是否为本周
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否为本周
 */
export function isThisWeek(date) {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'week')
}

/**
 * 检查是否为本月
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否为本月
 */
export function isThisMonth(date) {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'month')
}

/**
 * 检查是否为本年
 * @param {string|Date} date - 日期
 * @returns {boolean} 是否为本年
 */
export function isThisYear(date) {
  if (!date) return false
  return dayjs(date).isSame(dayjs(), 'year')
}

/**
 * 获取日期范围
 * @param {string} range - 范围类型 (today, yesterday, week, month, year)
 * @returns {object} 开始和结束日期
 */
export function getDateRange(range) {
  const now = dayjs()
  
  switch (range) {
    case 'today':
      return {
        start: now.startOf('day'),
        end: now.endOf('day')
      }
    case 'yesterday':
      const yesterday = now.subtract(1, 'day')
      return {
        start: yesterday.startOf('day'),
        end: yesterday.endOf('day')
      }
    case 'week':
      return {
        start: now.startOf('week'),
        end: now.endOf('week')
      }
    case 'month':
      return {
        start: now.startOf('month'),
        end: now.endOf('month')
      }
    case 'year':
      return {
        start: now.startOf('year'),
        end: now.endOf('year')
      }
    default:
      return {
        start: now.startOf('day'),
        end: now.endOf('day')
      }
  }
}

/**
 * 格式化持续时间
 * @param {number} seconds - 秒数
 * @returns {string} 格式化的持续时间
 */
export function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '0秒'
  
  const days = Math.floor(seconds / (24 * 60 * 60))
  const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
  const minutes = Math.floor((seconds % (60 * 60)) / 60)
  const secs = seconds % 60
  
  let result = ''
  
  if (days > 0) result += `${days}天`
  if (hours > 0) result += `${hours}小时`
  if (minutes > 0) result += `${minutes}分钟`
  if (secs > 0 || result === '') result += `${secs}秒`
  
  return result
}

/**
 * 获取当前时间戳
 * @returns {number} 当前时间戳
 */
export function getCurrentTimestamp() {
  return dayjs().valueOf()
}

/**
 * 时间戳转日期
 * @param {number} timestamp - 时间戳
 * @returns {Date} 日期对象
 */
export function timestampToDate(timestamp) {
  return dayjs(timestamp).toDate()
}

/**
 * 日期转时间戳
 * @param {string|Date} date - 日期
 * @returns {number} 时间戳
 */
export function dateToTimestamp(date) {
  return dayjs(date).valueOf()
}

/**
 * 设置时区
 * @param {string} timezone - 时区
 */
export function setTimezone(timezone = 'Asia/Shanghai') {
  dayjs.tz.setDefault(timezone)
}

/**
 * 获取时区时间
 * @param {string|Date} date - 日期
 * @param {string} timezone - 时区
 * @returns {dayjs.Dayjs} 时区时间
 */
export function getTimezoneTime(date, timezone = 'Asia/Shanghai') {
  return dayjs(date).tz(timezone)
}

// 默认设置时区
setTimezone()

export default {
  formatDateTime,
  formatDate,
  formatTime,
  getRelativeTime,
  getTimeDiff,
  isExpired,
  isExpiringSoon,
  getRemainingDays,
  getRemainingTime,
  formatRemainingTime,
  getMonthName,
  getWeekdayName,
  isToday,
  isYesterday,
  isThisWeek,
  isThisMonth,
  isThisYear,
  getDateRange,
  formatDuration,
  getCurrentTimestamp,
  timestampToDate,
  dateToTimestamp,
  setTimezone,
  getTimezoneTime
}
