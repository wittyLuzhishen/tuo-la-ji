// 全局变量
let socket = null;
let currentUser = null;
let currentRoomId = null;
let roomList = [];
let socketUserId = null;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Socket.IO连接
    initSocketConnection();
    
    // 设置事件监听器
    setupEventListeners();
    
    // 初始化页面
    initializePage();
});

// 初始化Socket.IO连接
function initSocketConnection() {
    // 使用common.js中的函数初始化连接
    socket = window.initSocketConnection();
    
    // 设置Socket事件监听器
    setupSocketListeners();
}

// 设置Socket事件监听器
function setupSocketListeners() {
    // 使用common.js中的函数设置基础事件监听器
    setupBasicSocketListeners(
        socket,
        // 连接成功回调
        function() {
            // 连接成功后尝试使用保存的ID进行重连
            attemptReconnectWithSavedId(socket);
        },
        // 连接断开回调
        function() {
            console.log('与服务器连接断开');
        },
        // 用户ID分配回调
        function(userId) {
            socketUserId = userId;
            console.log('收到服务器分配的user_id:', socketUserId);
            
            // 在收到user_id后再进行后续操作
            // 如果用户已登录，重新设置用户名
            if (currentUser) {
                socket.emit(ClientMessageType.SetUserInfo, { 
                    [ClientDataKey.UserID]: userId, 
                    [ClientDataKey.Username]: currentUser.username,
                    [ClientDataKey.AvatarURL]: currentUser.avatar_url
                });
            }
            // 获取房间列表
            getRoomList();
        },
        // 用户信息更新回调
        function(user) {
            currentUser = user;
            updateUserDisplay();
        }
    );
    
    // 房间列表更新
    socket.on(ServerMessageType.RoomList, function(data) {
        roomList = data.rooms;
        displayRoomList(roomList);
    });

    // 房间创建成功
    socket.on(ServerMessageType.RoomCreated, function(data) {
        currentRoomId = data.room_id;
        // 跳转到游戏房间页面
        window.location.href = '/room?id=' + currentRoomId;
    });

    // 加入房间成功
    socket.on(ServerMessageType.RoomJoined, function(data) {
        currentRoomId = data.room_id;
        // 跳转到游戏房间页面
        window.location.href = '/room?id=' + currentRoomId;
    });

    // 错误处理
    socket.on(ServerMessageType.Error, function(data) {
        alert(data.message);
    });
}

// 设置页面事件监听器
function setupEventListeners() {
    // 用户设置相关
    document.getElementById('confirm-user-setup').addEventListener('click', confirmUserSetup);
    document.getElementById('cancel-user-setup').addEventListener('click', function() {
        hideModal('user-setup-modal');
    });
    
    // 头像上传相关
    document.getElementById('upload-avatar-btn').addEventListener('click', function() {
        const fileInput = document.getElementById('avatar-upload');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('请选择一个文件');
            return;
        }
        
        // 使用common.js中的函数上传头像
        if (typeof uploadAvatar === 'function') {
            // 为了保持与room.js一致的行为，这里我们不传入回调函数
            // 让uploadAvatar函数自己处理UI更新和提示
            uploadAvatar(socket, getUserId(), getCurrentUser()?.username || '');
        }
    });
    
    // 房间列表相关
    document.getElementById('refresh-room-list-btn').addEventListener('click', getRoomList);
    document.getElementById('apply-filters-btn').addEventListener('click', applyFilters);
    document.getElementById('reset-filters-btn').addEventListener('click', resetFilters);
    
    // 创建房间相关
    document.getElementById('create-room-btn').addEventListener('click', showCreateRoomModal);
    document.getElementById('confirm-create-room-btn').addEventListener('click', createRoom);
    document.getElementById('cancel-create-room-btn').addEventListener('click', function() {
        hideModal('create-room-modal');
    });
    
    // 游戏规则相关
    document.getElementById('view-rules-btn').addEventListener('click', function() {
        showModal('rules-modal');
    });
    document.getElementById('close-rules-modal-btn').addEventListener('click', function() {
        hideModal('rules-modal');
    });
    
    // 模态框外部点击关闭
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
}

// 初始化页面
function initializePage() {
    // 加载预设头像
    loadPresetAvatars();
    
    // 检查是否已登录
    checkUserLogin();
    
    // 获取房间列表
    getRoomList();
}

// 检查用户登录状态
function checkUserLogin() {
    // 使用common.js中的函数获取用户信息
    currentUser = getCurrentUser();
    if (currentUser) {
        updateUserDisplay();
    } else {
        // 显示用户设置模态框
        document.getElementById('user-setup-modal').style.display = 'block';
    }
}

// 更新用户显示
function updateUserDisplay() {
    if (currentUser) {
        document.getElementById('username-display').textContent = currentUser.username;
        document.getElementById('user-coins').textContent = '金币: ' + (currentUser.coins || 0);
        if (currentUser.avatar_url) {
            document.getElementById('user-avatar').src = currentUser.avatar_url;
        }
        // 使用common.js中的函数保存用户信息
        saveCurrentUser(currentUser);
    }
}

// 确认用户设置
function confirmUserSetup() {
    const username = document.getElementById('username-input').value.trim();
    
    // 使用common.js中的函数验证用户名
    const validationResult = validateUsername(username);
    if (!validationResult.valid) {
        document.getElementById('username-error').textContent = validationResult.error;
        document.getElementById('username-error').style.display = 'block';
        return;
    }
    
    // 获取选中的头像
    let selectedAvatarUrl = '';
    const selectedAvatar = document.querySelector('.avatar-option.selected img');
    if (selectedAvatar) {
        selectedAvatarUrl = selectedAvatar.src;
    } else {
        // 如果没有选中的头像，使用预览图
        selectedAvatarUrl = document.getElementById('avatar-preview').src;
    }
    
    // 使用common.js中的函数创建用户对象
    currentUser = createUserObject(username, selectedAvatarUrl);
    updateUserDisplay();
    
    // 通过Socket.IO设置用户名和头像
    const userId = getUserId();
    console.log('使用用户ID:', userId);
    
    // 如果Socket已连接，统一发送更新消息
    if (socket && socket.connected && userId) {
        // 使用getCleanAvatarUrl处理头像URL（如果函数可用）
        const cleanAvatarUrl = typeof getCleanAvatarUrl === 'function' ? getCleanAvatarUrl(selectedAvatarUrl) : selectedAvatarUrl;
        socket.emit(ClientMessageType.SetUserInfo, { 
            [ClientDataKey.UserID]: userId,
            [ClientDataKey.Username]: username,
            [ClientDataKey.AvatarURL]: cleanAvatarUrl
        });
    }
    
    // 关闭模态框
    hideModal('user-setup-modal');
}

// 加载预设头像
function loadPresetAvatars() {
    // 使用common.js中的函数加载预设头像
    window.loadPresetAvatars('.avatar-grid', function(avatarUrl) {
        // 只更新预览，不自动保存
        document.getElementById('avatar-preview').src = avatarUrl;
    });
}

// 上传头像 - 统一到用户信息面板中处理

// 获取房间列表
function getRoomList() {
    socket.emit(ClientMessageType.GetRoomList);
}

// 显示房间列表
function displayRoomList(rooms) {
    const tbody = document.getElementById('room-list-tbody');
    const noRoomsMessage = document.getElementById('no-rooms-message');
    
    // 清空现有列表
    tbody.innerHTML = '';
    
    // 添加参数检查，确保rooms是数组
    if (!Array.isArray(rooms) || rooms.length === 0) {
        noRoomsMessage.style.display = 'block';
        return;
    }
    
    noRoomsMessage.style.display = 'none';
    
    rooms.forEach(room => {
        const row = document.createElement('tr');
        
        // 房间名称
        const nameCell = document.createElement('td');
        nameCell.textContent = room.name;
        row.appendChild(nameCell);
        
        // 房主
        const ownerCell = document.createElement('td');
        ownerCell.textContent = room.owner || '未知';
        row.appendChild(ownerCell);
        
        // 玩家数量
        const playerCountCell = document.createElement('td');
        playerCountCell.textContent = `${room.player_count || 0}/${room.max_players || 6}`;
        row.appendChild(playerCountCell);
        
        // 房间状态
        const statusCell = document.createElement('td');
        const status = room.status === 'playing' ? '游戏中' : '等待中';
        statusCell.textContent = status;
        row.appendChild(statusCell);
        
        // 操作按钮
        const actionCell = document.createElement('td');
        const joinButton = document.createElement('button');
        joinButton.className = 'btn btn-primary btn-sm';
        joinButton.textContent = '加入房间';
        joinButton.addEventListener('click', function() {
            joinRoom(room.id);
        });
        actionCell.appendChild(joinButton);
        row.appendChild(actionCell);
        
        tbody.appendChild(row);
    });
}

// 应用筛选
function applyFilters() {
    const nameFilter = document.getElementById('filter-room-name').value.toLowerCase();
    const playerCountFilter = document.getElementById('filter-player-count').value;
    const statusFilter = document.getElementById('filter-room-status').value;
    
    const filteredRooms = roomList.filter(room => {
        let matchName = !nameFilter || room.name.toLowerCase().includes(nameFilter);
        let matchPlayerCount = !playerCountFilter || room.player_count == playerCountFilter;
        let matchStatus = !statusFilter || room.status === statusFilter;
        
        return matchName && matchPlayerCount && matchStatus;
    });
    
    displayRoomList(filteredRooms);
}

// 重置筛选
function resetFilters() {
    document.getElementById('filter-room-name').value = '';
    document.getElementById('filter-player-count').value = '';
    document.getElementById('filter-room-status').value = '';
    displayRoomList(roomList);
}

// 显示创建房间模态框
function showCreateRoomModal() {
    showModal('create-room-modal');
}

// 创建房间
function createRoom() {
    const roomName = document.getElementById('new-room-name').value.trim();
    const maxPlayers = parseInt(document.getElementById('new-room-max-players').value);
    const settings235Greater = document.getElementById('new-room-235-greater').checked;
    const initialCoins = parseInt(document.getElementById('new-room-initial-coins').value);
    const baseBet = parseInt(document.getElementById('new-room-base-bet').value);
    const maxBet = parseInt(document.getElementById('new-room-max-bet').value);
    const maxHands = parseInt(document.getElementById('new-room-max-hands').value);
    const maxPotAmount = parseInt(document.getElementById('new-room-max-pot-amount').value);
    
    if (!roomName) {
        alert('请输入房间名称');
        return;
    }
    
    // 通过Socket.IO创建房间
    socket.emit(ClientMessageType.CreateRoom, {
        [ClientDataKey.RoomName]: roomName,
        max_players: maxPlayers,
        settings: {
            '235_greater': settings235Greater,
            initial_coins: initialCoins,
            base_bet: baseBet,
            max_bet: maxBet,
            max_hands: maxHands,
            max_pot_amount: maxPotAmount
        }
    });
    
    // 关闭模态框
    document.getElementById('create-room-modal').style.display = 'none';
}

// 加入房间
function joinRoom(roomId) {
    if (!currentUser) {
        alert('请先设置用户名');
        document.getElementById('user-setup-modal').style.display = 'block';
        return;
    }
    
    // 通过Socket.IO加入房间
    socket.emit(ClientMessageType.JoinRoom, { [ClientDataKey.RoomID]: roomId });
}