# 校园二手交易平台 - 前端构建镜像
# 构建 Vue3 静态文件后拷贝到卷 /output，供 Nginx 挂载

# ---------- 构建阶段 ----------
FROM node:20-alpine AS build

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY package.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm install

# 复制源码并构建
COPY . .
RUN npm run build

# ---------- 输出阶段 ----------
FROM alpine:3.20

WORKDIR /output
# 构建产物暂存到 /app-dist（挂载卷会覆盖 /output，运行时再拷贝）
COPY --from=build /app/dist /app-dist

CMD ["sh", "-c", "cp -r /app-dist/. /output/ && echo 'frontend build output copied'"]