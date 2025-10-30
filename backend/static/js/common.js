// 通用工具函数
// 包含：本地存储用户信息、连接服务器、通过服务器重连接口获得user_id等功能

//#region 用户信息本次存储相关开始
// 统一的用户信息存储键名
const USER_INFO_KEY = 'userInfo';

/**
 * 获取当前用户信息
 * @returns {Object|null} 用户信息对象，如果不存在则返回null
 */
function getCurrentUser() {
    try {
        const userInfo = localStorage.getItem(USER_INFO_KEY);
        return userInfo ? JSON.parse(userInfo) : {};
    } catch (error) {
        console.error('获取当前用户信息时发生错误:', error);
        return {};
    }
}

/**
 * 保存当前用户信息
 * @param {Object} userInfo - 用户信息对象
 */
function saveCurrentUser(userInfo) {
    try {
        console.log('保存用户信息:', userInfo);
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
    } catch (error) {
        console.error('保存当前用户信息时发生错误:', error);
    }
}

/**
 * 清除用户信息
 */
function clearUserInfo() {
    try {
        localStorage.removeItem(USER_INFO_KEY);
    } catch (error) {
        console.error('清除用户信息时发生错误:', error);
    }
}

/**
 * 创建用户对象
 * @param {string} username - 用户名
 * @param {string} avatar_url - 头像URL
 * @param {string} user_id - 用户ID（可选）
 * @returns {Object} 用户对象
 */
function createUserInfoObject(username, avatar_url, user_id = null) {
    const userObject = {
        [ClientDataKey.Username]: username,
        [ClientDataKey.AvatarURL]: avatar_url
    };
    if (user_id) {
        userObject[ClientDataKey.UserID] = user_id;
    }
    console.log('创建用户对象:', userObject);
    return userObject;
}

/**
 * 获取用户ID
 * @returns {string|null} 用户ID，如果不存在则返回null
 */
function getUserId() {
    try {
        const userInfo = getCurrentUser();
        if (userInfo) {
            return userInfo[ClientDataKey.UserID] || '';
        }
        return '';
    } catch (error) {
        console.error('获取用户ID时发生错误:', error);
        return '';
    }
}

/**
 * 保存用户ID
 * @param {string} userId - 用户ID
 */
function saveUserId(userId) {
    try {
        console.log('保存用户ID:', userId);
        const userInfo = localStorage.getItem(USER_INFO_KEY);
        if (userInfo) {
            const parsedInfo = JSON.parse(userInfo);
            parsedInfo[ClientDataKey.UserID] = userId;
            saveCurrentUser(parsedInfo);
        } else {
            saveCurrentUser(createUserInfoObject('', '', userId));
        }
    } catch (error) {
        console.error('保存用户ID时发生错误:', error);
        saveCurrentUser(createUserInfoObject('', '', userId));
    }
}
//#endregion 用户信息本次存储相关结束

//#region socketio 连接相关
/**
 * 初始化Socket连接
 * @param {string} serverUrl - 服务器URL
 * @param {Object} options - Socket连接选项
 * @returns {Object|null} Socket实例或null
 */
function initSocketConnection(serverUrl = '/', options = {},
    onDisconnectCallback, onConnectErrorCallback) {
    try {
        console.log('初始化Socket连接:', serverUrl, options);

        // 检查socket.io是否已加载
        if (typeof io === 'undefined') {
            console.warn('Socket.IO 未加载，返回null');
            return null;
        }

        // 创建Socket实例
        const socket = io(serverUrl, options);

        // 连接成功事件
        socket.on(ServerMessageType.Connect, function () {
            console.log('Socket连接成功');
            try {
                sendReconnectWithID();
            } catch (error) {
                console.error('连接成功回调函数执行时发生错误:', error);
            }
        });

        // 连接断开事件
        socket.on(ServerMessageType.Disconnect, function (reason) {
            console.log('Socket连接断开:', reason);
            if (typeof onDisconnectCallback === 'function') {
                try {
                    onDisconnectCallback(reason);
                } catch (error) {
                    console.error('断开连接回调函数执行时发生错误:', error);
                }
            }
        });

        // 添加连接错误处理，但不中断程序
        socket.on(ServerMessageType.ConnectError, function (error) {
            console.warn('Socket连接错误:', error.message || error);
            // 不抛出错误，允许程序继续运行
            if (typeof onConnectErrorCallback === 'function') {
                try {
                    onConnectErrorCallback(error);
                } catch (error) {
                    console.error('连接错误回调函数执行时发生错误:', error);
                }
            }
        });

        // 定时检查socket连接
        setTimeout(() => {
            if (socket && !socket.connected) {
                console.warn('Socket连接超时，可能需要启动服务器或检查网络连接');
                // 不强制断开连接，让Socket.io尝试重连
            }
        }, options.reconnectionAttempts * options.reconnectionDelay || 5000);

        return socket;
    } catch (error) {
        console.error('初始化Socket连接时发生错误:', error);
        // 返回null而不是抛出错误，允许程序在没有Socket的情况下继续运行
        return null;
    }
}

/**
 * 设置Socket事件监听器
 * @param {Object} socket - Socket实例
 * @param {Object} eventHandlers - 事件处理函数对象，格式为{事件类型: 处理函数}
 */
function setupSocketListeners(socket, eventHandlers = {}) {
    if (!socket) {
        console.error('Socket实例不存在');
        return;
    }

    // 默认的事件处理函数
    const defaultHandlers = {
        // 可以添加默认的事件处理逻辑
        [ServerMessageType.UserIDAssigned]: receiveUserIDAssigned,
    };

    // 合并用户提供的处理函数和默认处理函数
    const handlers = { ...defaultHandlers, ...eventHandlers };

    // 为每个事件添加监听器
    /**
     * 创建安全的事件处理函数，捕获并记录异常
     * @param {Function} handler - 原始事件处理函数
     * @param {string} event - 事件名称
     * @returns {Function} 包装后的安全处理函数
     */
    function createSafeEventHandler(handler, event) {
        return function (...args) {
            try {
                // 保留原始this上下文并传递所有参数
                return handler.apply(this, args);
            } catch (error) {
                console.error(`处理事件 ${event} 时发生错误:`, error);
                // 可选：添加更多错误处理逻辑，如错误上报等
                // 不抛出异常，确保其他事件处理不受影响
            }
        };
    }

    // 为每个事件添加安全的监听器
    for (const [event, handler] of Object.entries(handlers)) {
        if (typeof handler === 'function') {
            // 使用包装函数来捕获异常
            socket.on(event, createSafeEventHandler(handler, event));
        }
    }
}

function sendReconnectWithID() {
    let savedUserId = getUserId();
    savedUserId = savedUserId || '';
    console.log(`发送重新连接请求, 用户ID: ${savedUserId}`);
    socket.emit(ClientMessageType.ReconnectWithID, {
        [ClientDataKey.UserID]: savedUserId
    });
}

function receiveUserIDAssigned(data) {
    if (data[ServerDataKey.UserID]) {
        console.log('服务器分配的用户ID:', data[ServerDataKey.UserID]);
        saveUserId(data[ServerDataKey.UserID]);
        return;
    }
    console.warn('服务器未返回用户ID');
}
//#endregion socketio 连接相关结束


//#region  模态对话框显示
/**
 * 显示模态框
 * @param {string} modalId - 模态框的ID
 */
function showModal(modalId) {
    try {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            modal.style.display = 'block';
            // 添加背景遮罩
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = `${modalId}-backdrop`;
            document.body.appendChild(backdrop);
            // 防止背景滚动
            document.body.style.overflow = 'hidden';
        }
    } catch (error) {
        console.error('显示模态框时发生错误:', error);
    }
}

/**
 * 隐藏模态框
 * @param {string} modalId - 模态框的ID
 */
function hideModal(modalId) {
    try {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            // 移除背景遮罩
            const backdrop = document.getElementById(`${modalId}-backdrop`);
            if (backdrop) {
                backdrop.remove();
            }
            // 恢复背景滚动
            document.body.style.overflow = '';
        }
    } catch (error) {
        console.error('隐藏模态框时发生错误:', error);
    }
}

/**
 * 显示提示消息（Toast）
 * @param {string} title - 提示标题
 * @param {string} message - 提示内容
 * @param {number} duration - 显示时长（毫秒），默认3000ms
 */
function showToast(title, message, duration = 3000) {
    try {
        // 检查是否已存在toast容器，如果不存在则创建
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            toastContainer.style.display = 'flex';
            toastContainer.style.flexDirection = 'column';
            toastContainer.style.gap = '10px';
            document.body.appendChild(toastContainer);
        }

        // 创建toast元素
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.padding = '12px 20px';
        toast.style.borderRadius = '6px';
        toast.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        toast.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        toast.style.cursor = 'pointer';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        toast.style.transition = 'opacity 0.3s, transform 0.3s';

        // 根据标题设置样式
        if (title === '错误') {
            toast.style.backgroundColor = '#f8d7da';
            toast.style.border = '1px solid #f5c6cb';
            toast.style.color = '#721c24';
        } else if (title === '警告') {
            toast.style.backgroundColor = '#fff3cd';
            toast.style.border = '1px solid #ffeaa7';
            toast.style.color = '#856404';
        } else if (title === '提示') {
            toast.style.backgroundColor = '#d1ecf1';
            toast.style.border = '1px solid #bee5eb';
            toast.style.color = '#0c5460';
        } else {
            toast.style.backgroundColor = '#f8f9fa';
            toast.style.border = '1px solid #e9ecef';
            toast.style.color = '#212529';
        }

        // 设置toast内容
        toast.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">${title}</div>
            <div style="font-size: 14px;">${message}</div>
        `;

        // 添加到容器
        toastContainer.appendChild(toast);

        // 触发重排，然后显示动画
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);

        // 设置自动关闭
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px)';

            // 动画结束后移除元素
            setTimeout(() => {
                if (toast.parentNode === toastContainer) {
                    toastContainer.removeChild(toast);
                }

                // 如果容器为空，移除容器
                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        }, duration);

        // 添加点击关闭
        toast.addEventListener('click', () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px)';

            setTimeout(() => {
                if (toast.parentNode === toastContainer) {
                    toastContainer.removeChild(toast);
                }

                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        });

    } catch (error) {
        console.error('显示Toast时发生错误:', error);
        // 降级为alert
        alert(`${title}: ${message}`);
    }
}
//#endregion  模态对话框显示

//#region 导出
window.getUserId = getUserId;
window.saveUserId = saveUserId;
window.getCurrentUser = getCurrentUser;
window.saveCurrentUser = saveCurrentUser;
window.clearUserInfo = clearUserInfo;
window.createUserInfoObject = createUserInfoObject;
window.initSocketConnection = initSocketConnection;
window.setupSocketListeners = setupSocketListeners;
window.showModal = showModal;
window.hideModal = hideModal;
window.showToast = showToast;

// 常量也挂载到window上
window.USER_INFO_KEY = USER_INFO_KEY;

//#endregion 导出
