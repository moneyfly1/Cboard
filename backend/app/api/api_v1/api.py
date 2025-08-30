from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, subscriptions, orders, packages, nodes, admin, notifications, config, statistics, payment, settings

api_router = APIRouter()

# 用户端API
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["订阅"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单"])
api_router.include_router(packages.router, prefix="/packages", tags=["套餐"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["节点"])

# 管理端API
api_router.include_router(admin.router, prefix="/admin", tags=["管理端"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])
api_router.include_router(config.router, prefix="/config", tags=["配置"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["统计"])
api_router.include_router(payment.router, prefix="/payment", tags=["支付"])
api_router.include_router(settings.router, prefix="/settings", tags=["设置"]) 