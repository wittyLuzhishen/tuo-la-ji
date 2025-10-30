// 用户信息相关的工具函数

// 统一的用户信息存储键名
export const USER_INFO_KEY = 'userInfo';

/**
 * 获取用户ID
 * @returns {string|null} 用户ID，如果不存在则返回null
 */
export function getUserId() {
    try {
        const userInfo = localStorage.getItem(USER_INFO_KEY);
        return userInfo ? JSON.parse(userInfo).user_id : null;
    } catch (error) {
        console.error('获取用户ID失败:', error);
        return null;
    }
}

/**
 * 保存用户ID
 * @param {string} userId - 用户ID
 */
export function saveUserId(userId) {
    try {
        let userInfo = {};
        const existingInfo = localStorage.getItem(USER_INFO_KEY);
        if (existingInfo) {
            userInfo = JSON.parse(existingInfo);
        }
        userInfo.user_id = userId;
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
    } catch (error) {
        console.error('保存用户ID失败:', error);
    }
}

/**
 * 获取当前用户信息
 * @returns {Object|null} 用户对象，如果不存在则返回null
 */
export function getCurrentUser() {
    try {
        const savedUser = localStorage.getItem(USER_INFO_KEY);
        return savedUser ? JSON.parse(savedUser) : null;
    } catch (error) {
        console.error('获取用户信息失败:', error);
        return null;
    }
}

/**
 * 保存当前用户信息
 * @param {Object} userInfo - 用户信息对象
 */
export function saveCurrentUser(userInfo) {
    try {
        // 只保存必要的用户信息，不包含金币
        const userDataToSave = {
            user_id: userInfo.user_id,
            username: userInfo.username,
            avatar_url: userInfo.avatar_url
        };
        localStorage.setItem(USER_INFO_KEY, JSON.stringify(userDataToSave));
    } catch (error) {
        console.error('保存用户信息失败:', error);
    }
}

/**
 * 清除用户信息
 */
export function clearUserInfo() {
    localStorage.removeItem(USER_INFO_KEY);
}

/**
 * 创建用户对象
 * @param {string} username - 用户名
 * @param {string} avatar_url - 头像URL
 * @param {string} user_id - 用户ID（可选）
 * @returns {Object} 用户对象
 */
export function createUserObject(username, avatar_url, user_id = null) {
    const userObject = {
        username: username,
        avatar_url: avatar_url
    };
    if (user_id) {
        userObject.user_id = user_id;
    }
    return userObject;
}

/**
 * 初始化Socket.IO连接
 * @param {Object} options - 选项对象
 * @param {Function} options.onUserIdAssigned - 用户ID分配回调
 * @param {Function} options.customConnectedHandler - 自定义连接处理回调
 * @returns {Object|null} Socket对象或null
 */
export function initSocketConnection(options = {}) {
    // 确保Socket.IO已加载
    if (typeof io === 'undefined') {
        console.error('Socket.IO未加载');
        return null;
    }

    // 创建Socket.IO连接
    const socket = io();
    
    // 连接成功
    socket.on('connect', function() {
        console.log('连接成功');
    });
    
    // 接收服务器分配的user_id并存储
    socket.on(ServerMessageType.UserIDAssigned, function(data) {
        const user_id = data.user_id;
        console.log('收到服务器分配的user_id:', user_id);
        saveUserId(user_id);
        
        if (typeof options.onUserIdAssigned === 'function') {
            options.onUserIdAssigned(data); // 传递完整数据对象
        }
    });
    
    return socket;
}

/**
 * 设置Socket.IO基础事件监听器
 * @param {Object} socket - Socket.IO对象
 * @param {Object} options - 选项对象
 * @param {Function} options.onConnect - 连接成功回调
 * @param {Function} options.onDisconnect - 连接断开回调
 * @param {Function} options.onUserIdAssigned - 用户ID分配回调
 * @param {Function} options.onUserInfoUpdated - 用户信息更新回调
 * @param {Function} options.onUsernameError - 用户名错误回调
 * @param {Function} options.customConnectedHandler - 自定义连接处理回调
 */
export function setupBasicSocketListeners(socket, options = {}) {
    if (!socket) return;

    const { onConnect, onDisconnect, onUserIdAssigned, onUserInfoUpdated, onUsernameError, customConnectedHandler } = options;

    // 连接成功
    socket.on('connect', function() {
        console.log('已连接到服务器');
        if (typeof onConnect === 'function') {
            onConnect();
        }
    });

    // 接收服务器分配的user_id并存储
    socket.on(ServerMessageType.UserIDAssigned, function(data) {
        const user_id = data.user_id;
        console.log('收到服务器分配的user_id:', user_id);
        saveUserId(user_id);
        if (typeof onUserIdAssigned === 'function') {
            onUserIdAssigned(data); // 传递完整数据对象
        }
    });

    // 用户名设置成功/用户信息更新
    socket.on(ServerMessageType.UserInfoUpdated, function(data) {
        // 确保数据格式与我们的期望一致
        const user = {
            username: data.user.username,
            avatar_url: data.user.avatar || data.user.avatar_url,
            coins: data.user.coins || 0,
            user_id: data.user.user_id
        };
        saveCurrentUser(user);
        if (typeof onUserInfoUpdated === 'function') {
            onUserInfoUpdated(user);
        }
    });

    // 连接断开
    socket.on('disconnect', function() {
        console.log('与服务器连接断开');
        if (typeof onDisconnect === 'function') {
            onDisconnect();
        }
    });

    // 连接错误
    socket.on('connect_error', function(error) {
        console.log('连接错误:', error);
    });
    
    // 服务器连接确认
    socket.on(ServerMessageType.Connected, function(data) {
        console.log('收到服务器连接确认:', data);
        
        // 尝试使用保存的用户ID进行重连
        attemptReconnectWithSavedId(socket);
        
        // 如果有自定义处理函数，调用它
        if (typeof customConnectedHandler === 'function') {
            customConnectedHandler(data);
        }
    });
    
    // 用户名错误
    socket.on(ServerMessageType.UsernameError, function(data) {
        console.log('用户名错误:', data);
        if (typeof onUsernameError === 'function') {
            onUsernameError(data);
        }
    });
}

/**
 * 使用保存的用户ID进行重连
 * @param {Object} socket - Socket.IO对象
 */
export function attemptReconnectWithSavedId(socket) {
    if (!socket) return;
    
    const savedUserId = getUserId();
    if (savedUserId) {
        console.log('使用保存的user_id进行重连:', savedUserId);
        socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: savedUserId });
    } else {
        console.log('没有保存的user_id，请求分配新ID');
        socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: null });
    }
}

/**
 * 获取清理后的头像URL（移除时间戳）
 * @param {string} avatarUrl - 头像URL
 * @returns {string} 清理后的头像URL
 */
export function getCleanAvatarUrl(avatarUrl) {
    if (!avatarUrl) return null;
    
    // 移除已有的时间戳参数，确保只保存基础URL
    let cleanAvatarUrl = avatarUrl;
    if (avatarUrl.includes('?')) {
        const urlParts = avatarUrl.split('?');
        const queryParams = new URLSearchParams(urlParts[1]);
        queryParams.delete('t'); // 删除时间戳参数

        if (queryParams.toString()) {
            cleanAvatarUrl = `${urlParts[0]}?${queryParams.toString()}`;
        } else {
            cleanAvatarUrl = urlParts[0];
        }
    }
    
    return cleanAvatarUrl;
}

/**
 * 设置头像URL（添加时间戳防止缓存）
 * @param {string} avatarUrl - 头像URL
 * @returns {string} 添加时间戳后的头像URL
 */
export function getAvatarUrlWithTimestamp(avatarUrl) {
    if (!avatarUrl) return null;
    
    // 先获取清理后的URL
    const cleanAvatarUrl = getCleanAvatarUrl(avatarUrl);

    // 添加新的时间戳防止浏览器缓存
    const timestamp = new Date().getTime();
    return cleanAvatarUrl.includes('?')
        ? `${cleanAvatarUrl}&t=${timestamp}`
        : `${cleanAvatarUrl}?t=${timestamp}`;
}

/**
 * 上传头像
 * @param {Object} socket - Socket.IO对象
 * @param {string} userId - 用户ID
 * @param {string} username - 用户名
 */
export function uploadAvatar(socket, userId, username) {
    console.log('点击上传头像按钮');
    const fileInput = document.getElementById('avatar-upload');
    if (!fileInput || fileInput.files.length === 0) {
        alert('请选择一个文件');
        return;
    }
    
    const file = fileInput.files[0];
    console.log('选择的文件:', file);
    const formData = new FormData();
    formData.append('file', file);

    console.log('Socket状态:', socket ? '已连接' : '未连接');
    console.log('User ID:', userId);

    // 上传文件
    console.log('开始上传文件到 /upload_avatar');
    fetch('/upload_avatar', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('上传响应状态:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }
        return response.json().catch(err => {
            console.error('解析JSON响应失败:', err);
            // 尝试获取原始文本
            return response.text().then(text => {
                console.log('原始响应文本:', text);
                throw new Error('服务器返回了非JSON响应');
            });
        });
    })
    .then(data => {
        console.log('上传成功，服务器返回:', data);
        if (data.avatar_url || data.url) {
            // 使用可能的头像URL字段
            const avatarUrl = data.avatar_url || data.url;
            // 添加时间戳防止浏览器缓存
            const avatarUrlWithTimestamp = getAvatarUrlWithTimestamp(avatarUrl);

            // 更新预览
            const avatarPreview = document.getElementById('avatar-preview');
            if (avatarPreview) {
                avatarPreview.src = avatarUrlWithTimestamp;
            }

            // 清除其他选中状态
            document.querySelectorAll('.avatar-option').forEach(option => {
                option.classList.remove('selected');
                if (option.querySelector('img')) {
                    option.querySelector('img').style.border = 'none';
                }
            });

            // 不单独更新头像，只更新预览和本地状态
            // 等待用户在信息面板中统一提交用户名和头像
            
            alert('头像上传成功，请在用户信息面板中点击确认按钮保存修改');
        } else {
            alert('头像上传失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        console.error('上传头像时发生错误:', error);
        alert('头像上传失败: ' + error.message);
    });
}

/**
 * 显示模态框
 * @param {string} modalId - 模态框ID
 */
export function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        modal.classList.add('show');
    }
}

/**
 * 隐藏模态框
 * @param {string} modalId - 模态框ID
 */
export function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
}

/**
 * 加载预设头像
 * @param {string} gridSelector - 头像网格的CSS选择器
 * @param {Function} onAvatarSelect - 头像选择回调函数
 */
export function loadPresetAvatars(gridSelector, onAvatarSelect) {
    const avatarGrid = document.querySelector(gridSelector);
    if (!avatarGrid) return;
    
    const presetAvatars = [
        '/static/avatars/default.svg',
        '/static/avatars/preset1.svg',
        '/static/avatars/preset2.svg',
        '/static/avatars/preset3.svg',
        '/static/avatars/preset4.svg',
        '/static/avatars/tuolaji.png'
    ];
    
    presetAvatars.forEach(avatar => {
        const avatarOption = document.createElement('div');
        avatarOption.className = 'avatar-option';
        avatarOption.innerHTML = `<img src="${avatar}" alt="头像" style="width: 50px; height: 50px; cursor: pointer;">`;
        
        avatarOption.addEventListener('click', function() {
            if (typeof onAvatarSelect === 'function') {
                onAvatarSelect(avatar);
            }
        });
        
        avatarGrid.appendChild(avatarOption);
    });
}

/**
 * 验证用户名
 * @param {string} username - 用户名
 * @returns {Object} 包含valid和message属性的对象
 */
export function validateUsername(username) {
    if (!username || username.trim() === '') {
        return { valid: false, message: '用户名不能为空' };
    }
    
    if (username.length < 2) {
        return { valid: false, message: '用户名至少需要2个字符' };
    }
    
    if (username.length > 20) {
        return { valid: false, message: '用户名不能超过20个字符' };
    }
    
    if (!/^[a-zA-Z0-9_\u4e00-\u9fa5]+$/.test(username)) {
        return { valid: false, message: '用户名只能包含字母、数字、下划线和中文字符' };
    }
    
    return { valid: true, message: '' };
}

/**
 * 更新用户信息显示（从common.js导出）
 * @description 更新页面上的用户昵称和头像显示
 */
export function updateUserDisplayFromCommon() {
    // 获取当前用户信息
    const currentUser = getCurrentUser();
    if (!currentUser) return;
    
    // 更新用户名显示
    if (currentUser.username) {
        // 尝试不同的用户名字段ID
        const usernameElements = [
            document.getElementById('player-name'),
            document.getElementById('user-name'),
            document.getElementById('username')
        ];
        
        usernameElements.forEach(element => {
            if (element) {
                // 检查元素是否已经包含前缀，如果没有则添加
                if (!element.textContent.includes('玩家昵称：') && !element.textContent.includes('用户名：')) {
                    element.textContent = `玩家昵称：${currentUser.username}`;
                }
            }
        });
    }
    
    // 更新头像显示
    if (currentUser.avatar_url) {
        // 获取带有时间戳的头像URL，防止缓存问题
        const avatarUrlWithTimestamp = getAvatarUrlWithTimestamp(currentUser.avatar_url);
        
        // 尝试不同的头像元素ID
        const avatarElements = [
            document.getElementById('user-avatar'),
            document.getElementById('avatar-preview'),
            document.getElementById('player-avatar')
        ];
        
        avatarElements.forEach(element => {
            if (element) {
                element.src = avatarUrlWithTimestamp;
            }
        });
    }
}

// 保留兼容模式，将函数挂载到window对象上，确保旧代码仍然可以工作
(function() {
    const exportedFunctions = {
        getUserId,
        saveUserId,
        getCurrentUser,
        saveCurrentUser,
        clearUserInfo,
        createUserObject,
        initSocketConnection,
        setupBasicSocketListeners,
        attemptReconnectWithSavedId,
        getAvatarUrlWithTimestamp,
        getCleanAvatarUrl,
        uploadAvatar,
        showModal,
        hideModal,
        loadPresetAvatars,
        validateUsername,
        updateUserDisplayFromCommon
    };
    
    // 将所有函数挂载到window对象上
    for (const [key, value] of Object.entries(exportedFunctions)) {
        if (typeof window[key] === 'undefined') {
            window[key] = value;
        }
    }
})();
