// 全局变量
let socket = null;
let userId = null;
let roomId = null;
let currentUser = null;

// 当文档加载完成时执行
window.addEventListener('DOMContentLoaded', function() {
    console.log('房间页面加载完成');
    
    // 获取URL中的房间ID参数
    const urlParams = new URLSearchParams(window.location.search);
    roomId = urlParams.get('room_id');
    
    if (!roomId) {
        console.error('未找到房间ID');
        // 可以重定向回大厅或显示错误消息
        return;
    }
    
    console.log('当前房间ID:', roomId);
    
    // 初始化Socket连接
    initRoomSocket();
    
    // 从本地存储加载用户信息
    loadUserInfo();
    
    // 更新用户显示
    updateUserDisplay();
    
    // 绑定离开房间按钮事件
    const leaveRoomBtn = document.getElementById('leave-room-btn');
    if (leaveRoomBtn) {
        leaveRoomBtn.addEventListener('click', leaveRoom);
    }
    
    // 绑定座位点击事件
    bindSeatClickEvents();
    
    // 绑定准备按钮事件
    const readyBtn = document.getElementById('ready-btn');
    if (readyBtn) {
        readyBtn.addEventListener('click', toggleReadyStatus);
    }
});

/**
 * 初始化房间Socket连接
 */
function initRoomSocket() {
    console.log('初始化房间Socket连接');
    
    // 尝试从localStorage获取保存的用户ID
    userId = getUserId();
    
    // 初始化Socket连接
    socket = initSocketConnection('/', {
        query: {
            user_id: userId,
            room_id: roomId,
            location: 'room'
        },
        reconnectionAttempts: 3,
        reconnectionDelay: 1000
    });
    
    if (socket) {
        // 设置Socket监听器
        setupRoomSocketListeners(socket);
        
        // 尝试使用保存的ID重新连接
        attemptReconnectWithSavedId(socket, 
            function(receivedUserId) {
                // 重连成功回调
                userId = receivedUserId;
                saveUserId(userId);
                console.log('房间重连成功，用户ID:', userId);
                // 连接成功后加入房间
                joinRoom(roomId);
            },
            function(error) {
                // 重连失败回调
                console.warn('使用保存的ID重连失败:', error);
                // 降级到API方式获取用户ID
                fetchUserIdFromApi(
                    function(newUserId) {
                        userId = newUserId;
                        console.log('通过API获取用户ID成功:', userId);
                        // 尝试加入房间
                        joinRoom(roomId);
                    }
                );
            }
        );
    } else {
        console.warn('Socket初始化失败，尝试通过API获取用户ID');
        // 降级到API方式获取用户ID
        fetchUserIdFromApi(
            function(apiUserId) {
                userId = apiUserId;
                console.log('通过API获取用户ID成功:', userId);
                // 即使没有Socket连接，也尝试模拟加入房间的行为
                console.log('模拟加入房间:', roomId);
            }
        );
    }
}

/**
 * 设置房间Socket监听器
 */
function setupRoomSocketListeners(socket) {
    // 连接成功事件
    socket.on(ServerMessageType.ConnectSuccess, function(data) {
        console.log('连接成功:', data);
        
        // 获取用户ID
        userId = data[ServerDataKey.UserID] || userId;
        
        if (userId) {
            // 保存用户ID到localStorage
            saveUserId(userId);
            
            // 加入房间
            joinRoom(roomId);
        } else {
            console.error('未获取到用户ID');
        }
    });
    
    // 用户信息更新事件
    socket.on(ServerMessageType.UserInfoUpdated, function(data) {
        console.log('用户信息更新:', data);
        
        // 更新本地存储的用户信息
        if (data[ServerDataKey.UserID] === userId) {
            const userInfo = {
                user_id: userId,
                username: data[ServerDataKey.Username] || currentUser?.username,
                avatar_url: data[ServerDataKey.AvatarURL] || currentUser?.avatar_url
            };
            saveCurrentUser(userInfo);
            currentUser = userInfo;
            
            // 更新用户显示
            updateUserDisplay();
        }
    });
    
    // 房间信息更新事件
    socket.on(ServerMessageType.RoomDetails, function(data) {
        console.log('房间信息更新:', data);
        
        // 更新房间信息显示
        updateRoomDisplay(data);
    });
    
    // 游戏开始事件
    socket.on(ServerMessageType.GameStarted, function(data) {
        console.log('游戏开始:', data);
        
        // 处理游戏开始逻辑
        handleGameStart(data);
    });
    
    // 玩家离开事件
    socket.on(ServerMessageType.PlayerLeaved, function(data) {
        console.log('玩家离开:', data);
        
        // 更新房间玩家列表
        updatePlayerList();
    });
    
    // 连接错误事件
    socket.on(ServerMessageType.ConnectError, function(error) {
        console.error('连接错误:', error);
    });
    
    // 断开连接事件
    socket.on(ServerMessageType.Disconnect, function(reason) {
        console.log('断开连接:', reason);
    });
    
    // 错误消息事件
    socket.on(ServerMessageType.Error, function(data) {
        console.error('服务器错误:', data);
        alert('错误: ' + (data[ServerDataKey.ErrorMessage] || '未知错误'));
    });
}

/**
 * 从本地存储加载用户信息
 */
function loadUserInfo() {
    currentUser = getCurrentUser();
    userId = getUserId();
    
    if (!currentUser || !currentUser.username) {
        console.log('未找到用户信息，玩家将以匿名方式加入');
    }
}

/**
 * 更新用户显示
 */
function updateUserDisplay() {
    try {
        if (currentUser) {
            // 更新用户名显示
            const usernameDisplay = document.getElementById('username-display');
            if (usernameDisplay) {
                usernameDisplay.textContent = currentUser.username || '未登录';
            }
            
            // 更新头像显示
            const avatarDisplay = document.getElementById('user-avatar');
            if (avatarDisplay && currentUser.avatar_url) {
                avatarDisplay.src = getAvatarUrlWithTimestamp(currentUser.avatar_url);
            }
        }
    } catch (error) {
        console.error('更新用户显示时发生错误:', error);
    }
}

/**
 * 加入房间
 */
function joinRoom(roomId) {
    if (!socket || !socket.connected || !userId) {
        console.error('无法加入房间: 连接未建立或用户ID不存在');
        return;
    }
    
    console.log('加入房间:', roomId);
    socket.emit(ClientMessageType.JoinRoom, {
        [ClientDataKey.RoomID]: roomId,
        [ClientDataKey.UserID]: userId
    });
}

/**
 * 离开房间
 */
function leaveRoom() {
    if (!socket || !socket.connected) {
        // 即使Socket未连接，也尝试重定向回大厅
        window.location.href = '/templates/lobby.html';
        return;
    }
    
    console.log('离开房间:', roomId);
    socket.emit(ClientMessageType.LeaveRoom, {
        [ClientDataKey.RoomID]: roomId,
        [ClientDataKey.UserID]: userId
    });
    
    // 重定向回大厅
    setTimeout(() => {
        window.location.href = '/templates/lobby.html';
    }, 500);
}

/**
 * 绑定座位点击事件
 */
function bindSeatClickEvents() {
    const seats = document.querySelectorAll('.seat');
    seats.forEach(seat => {
        seat.addEventListener('click', function() {
            const seatIndex = parseInt(seat.dataset.seatIndex) || 0;
            sitDown(seatIndex);
        });
    });
}

/**
 * 坐下
 */
function sitDown(seatIndex) {
    if (!socket || !socket.connected || !userId) {
        console.error('无法坐下: 连接未建立或用户ID不存在');
        return;
    }
    
    console.log('坐下到座位:', seatIndex);
    socket.emit(ClientMessageType.SitDown, {
        [ClientDataKey.RoomID]: roomId,
        [ClientDataKey.UserID]: userId,
        [ClientDataKey.SeatIndex]: seatIndex
    });
}

/**
 * 站起
 */
function standUp() {
    if (!socket || !socket.connected || !userId) {
        console.error('无法站起: 连接未建立或用户ID不存在');
        return;
    }
    
    console.log('从座位站起');
    socket.emit(ClientMessageType.StandUp, {
        [ClientDataKey.RoomID]: roomId,
        [ClientDataKey.UserID]: userId
    });
}

/**
 * 切换准备状态
 */
function toggleReadyStatus() {
    if (!socket || !socket.connected || !userId) {
        console.error('无法切换准备状态: 连接未建立或用户ID不存在');
        return;
    }
    
    // 这里应该根据当前状态切换准备/取消准备
    // 简化版本，直接发送准备消息
    console.log('发送准备消息');
    socket.emit(ClientMessageType.Ready, {
        [ClientDataKey.RoomID]: roomId,
        [ClientDataKey.UserID]: userId
    });
}

/**
 * 更新房间显示
 */
function updateRoomDisplay(roomData) {
    // 更新房间名称
    const roomNameElement = document.getElementById('room-name');
    if (roomNameElement && roomData[ServerDataKey.RoomName]) {
        roomNameElement.textContent = roomData[ServerDataKey.RoomName];
    }
    
    // 更新玩家列表
    updatePlayerList(roomData[ServerDataKey.Players]);
}

/**
 * 更新玩家列表
 */
function updatePlayerList(players = []) {
    // 更新座位上的玩家信息
    players.forEach(player => {
        if (player.seat_index !== undefined) {
            const seatElement = document.querySelector(`.seat[data-seat-index="${player.seat_index}"]`);
            if (seatElement) {
                // 更新座位上的玩家信息
                // 这里应该根据实际的HTML结构进行更新
                console.log(`更新座位${player.seat_index}的玩家信息:`, player);
            }
        }
    });
}

/**
 * 处理游戏开始
 */
function handleGameStart(gameData) {
    console.log('处理游戏开始:', gameData);
    // 游戏开始的逻辑
}

// 导出必要的函数到window对象
window.leaveRoom = leaveRoom;
window.sitDown = sitDown;
window.standUp = standUp;
window.toggleReadyStatus = toggleReadyStatus;