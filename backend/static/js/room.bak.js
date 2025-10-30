import { 
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
} from './common.bak.js';

// 导入枚举定义
import { 
    ClientMessageType, 
    ClientDataKey, 
    ServerMessageType, 
    ServerDataKey 
} from './message_enums.js';

// 全局变量
let socket = null;
let username = null;
let currentRoomId = null;

/**
 * 动态定位游戏控制面板到当前玩家座位右侧
 * @param {HTMLElement} seat - 当前玩家座位元素
 */
function positionGameControls(seat) {
    const gameControls = document.getElementById('game-controls');
    if (!seat || !gameControls) return;

    // 获取座位的位置信息
    const seatRect = seat.getBoundingClientRect();

    // 计算游戏控制面板的位置 - 放在座位右侧紧挨着
    // 水平位置：座位右侧边缘 + 10px间距
    // 垂直位置：与座位顶部对齐
    const left = seatRect.right + 10;
    const top = seatRect.top;

    // 设置游戏控制面板的位置
    gameControls.style.left = `${left}px`;
    gameControls.style.top = `${top}px`;
    gameControls.style.bottom = 'auto';  // 清除之前的底部定位
    gameControls.style.right = 'auto';   // 清除之前的右侧定位
}

/**
 * 当窗口大小改变时，重新定位游戏控制面板
 */
function handleResize() {
    const currentSeat = document.querySelector('.current-player-seat');
    if (currentSeat) {
        positionGameControls(currentSeat);
    }
}

/**
 * 初始化游戏控制面板的拖动功能
 */
function initDraggableControls() {
    const gameControls = document.getElementById('game-controls');
    const controlsHeader = document.getElementById('controls-header');

    if (!gameControls || !controlsHeader) return;

    let isDragging = false;
    let offsetX, offsetY;

    // 鼠标按下事件，开始拖动
    controlsHeader.addEventListener('mousedown', function (e) {
        isDragging = true;

        // 计算鼠标相对于控制面板左上角的偏移量
        const rect = gameControls.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;

        // 添加临时样式，提高拖动时的可见性
        gameControls.style.opacity = '0.9';
        gameControls.style.zIndex = '1000'; // 拖动时置于最上层
    });

    // 鼠标移动事件，更新位置
    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;

        // 防止文本选择
        e.preventDefault();

        // 计算新位置，确保面板不会超出窗口边界
        const left = Math.max(0, Math.min(e.clientX - offsetX, window.innerWidth - gameControls.offsetWidth));
        const top = Math.max(0, Math.min(e.clientY - offsetY, window.innerHeight - gameControls.offsetHeight));

        // 设置控制面板位置
        gameControls.style.left = `${left}px`;
        gameControls.style.top = `${top}px`;
        gameControls.style.bottom = 'auto';
        gameControls.style.right = 'auto';
    });

    // 鼠标释放事件，结束拖动
    document.addEventListener('mouseup', function () {
        if (isDragging) {
            isDragging = false;
            // 恢复样式
            gameControls.style.opacity = '1';
            gameControls.style.zIndex = '20';
        }
    });
}

// 监听窗口大小改变事件，重新定位游戏控制面板
window.addEventListener('resize', handleResize);

// 页面加载完成后初始化拖动功能
window.addEventListener('load', initDraggableControls);
let user_id = null;
let current_room = null;
let is_owner = false;
let is_ready = false;
let is_playing = false;
let avatarSelected = false;
let selectedAvatarUrl = null;
let room_info = null;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 看牌按钮点击事件
    document.getElementById('look-cards-btn').addEventListener('click', function () {
        if (socket) {
            socket.emit(ClientMessageType.LookAtCards);
        }
    });

    // 开牌按钮点击事件
    document.getElementById('showdown-btn').addEventListener('click', function () {
        if (socket && user_id && currentRoomId) {
            socket.emit(ClientMessageType.Showdown, { 
                [ClientDataKey.RoomID]: currentRoomId, 
                [ClientDataKey.PlayerIdToBeShowdown]: user_id 
            });
        }
    });

    // 弃牌按钮点击事件
    document.getElementById('fold-btn').addEventListener('click', function () {
        if (socket) {
            socket.emit(ClientMessageType.Fold);
        }
    });

    // 跟注按钮点击事件
    document.getElementById('call-btn').addEventListener('click', function () {
        if (socket) {
            // 检查玩家是否看牌
            let lookedCards = false;
            if (room_info && room_info.game_data && room_info.game_data.looked_cards) {
                // looked_cards是set类型，需要转换为数组或使用has方法
                // 这里我们将其转换为数组以便使用includes方法
                const lookedCardsArray = Array.isArray(room_info.game_data.looked_cards) 
                    ? room_info.game_data.looked_cards 
                    : Array.from(room_info.game_data.looked_cards || []);
                lookedCards = lookedCardsArray.includes(user_id);
            }
            
            // 根据是否看牌显示不同的提示信息
            if (lookedCards) {
                if (!confirm('您已看牌，跟注金额将是当前底注的2倍。确定要跟注吗？')) {
                    return;
                }
            } else {
                if (!confirm('您未看牌，跟注金额将是当前底注。确定要跟注吗？')) {
                    return;
                }
            }
            
            // 发送跟注事件，后端会根据玩家是否看牌自动计算跟注金额
            socket.emit(ClientMessageType.Call);
        }
    });

    // 加注按钮点击事件
    document.getElementById('raise-btn').addEventListener('click', function () {
        const betAmount = document.getElementById('bet-amount').value.trim();
        if (socket && betAmount && !isNaN(betAmount) && parseInt(betAmount) > 0) {
            socket.emit(ClientMessageType.Raise, { [ClientDataKey.AddAmount]: parseInt(betAmount) });
        } else {
            alert('请输入有效的下注金额');
        }
    });
    // 房间页面不显示用户设置模态框

    // 保存原始用户名，用于后续比较
    let originalUsername = null;

    // 确认用户设置按钮点击事件
    document.getElementById('confirm-user-setup').addEventListener('click', function () {
    // 使用common.js中的函数处理用户设置确认
        const usernameInput = document.getElementById('username-input');
        const usernameError = document.getElementById('username-error');
        const newUsername = usernameInput.value.trim();

        // 隐藏之前的错误提示
        usernameError.style.display = 'none';

        // 使用common.js中的函数验证用户名
        if (typeof validateUsername === 'function') {
            const validationResult = validateUsername(newUsername);
            if (!validationResult.valid) {
                usernameError.textContent = validationResult.message;
                usernameError.style.display = 'block';
                return;
            }
        } else {
            // 备用验证逻辑 - 如果common.js中的函数不可用
            if (!newUsername) {
                usernameError.textContent = '请输入用户名';
                usernameError.style.display = 'block';
                return;
            }
        }

        if (!avatarSelected || !selectedAvatarUrl) {
            alert('请选择一个头像');
            return;
        }

        // 如果是首次设置，保存原始用户名
        if (originalUsername === null) {
            originalUsername = newUsername;
        }

        // 隐藏用户设置模态框
        document.getElementById('user-setup-modal').classList.remove('show');

        // 保存原始用户名，用于后续比较
        username = newUsername;
        if (originalUsername === null) {
            originalUsername = newUsername;
        }

        // 如果是首次设置，连接SocketIO进入房间
        if (socket === null) {
            connectSocket();
        } else if (user_id) {
            // 已连接：统一更新用户名和头像
            // 使用set_userinfo事件同时更新用户名和头像
            const cleanAvatarUrl = typeof getCleanAvatarUrl === 'function' ? getCleanAvatarUrl(selectedAvatarUrl) : selectedAvatarUrl;
            socket.emit(ClientMessageType.SetUserInfo, {
                [ClientDataKey.UserID]: user_id,
                [ClientDataKey.Username]: newUsername,
                [ClientDataKey.AvatarURL]: cleanAvatarUrl
            });
            
            // 保存用户信息到localStorage
            if (typeof getCurrentUser === 'function' && typeof saveCurrentUser === 'function' && typeof createUserObject === 'function') {
                const updatedUser = createUserObject(
                    newUsername,
                    cleanAvatarUrl,
                    user_id
                );
                saveCurrentUser(updatedUser);
                
                // 更新用户显示
                if (typeof updateUserDisplayFromCommon === 'function') {
                    updateUserDisplayFromCommon();
                }
            }
            
            originalUsername = newUsername;
        }
    });

    // 取消用户设置按钮点击事件
    document.getElementById('cancel-user-setup').addEventListener('click', function () {
        document.getElementById('user-setup-modal').classList.remove('show');
    });

    // 设置头像函数
    const originalSetAvatar = setAvatar;
    setAvatar = function (avatarUrl) {
        // 优先使用common.js中的函数处理头像URL
        let finalAvatarUrl;
        
        if (typeof getAvatarUrlWithTimestamp === 'function') {
            // 使用common.js中的函数获取带有时间戳的头像URL
            finalAvatarUrl = getAvatarUrlWithTimestamp(avatarUrl);
        } else {
            // 如果common.js中的函数不可用，使用降级方案
            // 移除已有的时间戳参数，避免重复添加
            let cleanAvatarUrl = avatarUrl;
            if (avatarUrl.includes('?')) {
                const urlParts = avatarUrl.split('?');
                const queryParams = new URLSearchParams(urlParts[1]);
                queryParams.delete('t');
                cleanAvatarUrl = urlParts[0];
                if (queryParams.toString()) {
                    cleanAvatarUrl += '?' + queryParams.toString();
                }
            }

            // 添加新的时间戳防止浏览器缓存
            const timestamp = new Date().getTime();
            finalAvatarUrl = cleanAvatarUrl.includes('?')
                ? `${cleanAvatarUrl}&t=${timestamp}`
                : `${cleanAvatarUrl}?t=${timestamp}`;
        }

        // 调用原函数设置头像
        originalSetAvatar(finalAvatarUrl);

        // 设置头像选择状态
        avatarSelected = true;
        selectedAvatarUrl = finalAvatarUrl;
        
        // 使用common.js中的函数保存用户信息
        if (typeof localStorage !== 'undefined' && getCurrentUser && saveCurrentUser && createUserObject) {
            // 获取当前用户信息
            const currentUser = getCurrentUser() || {};
            // 创建更新后的用户对象
            const updatedUser = createUserObject(
                currentUser.username || username || '',
                finalAvatarUrl,
                currentUser.user_id || user_id
            );
            // 保存到localStorage
            saveCurrentUser(updatedUser);
        }
    };



    // 起身按钮点击事件
    document.getElementById('stand-up-btn').addEventListener('click', function () {
        if (socket && user_id) {
            socket.emit(ClientMessageType.StandUp);
        }
    });

    // 准备按钮点击事件
    document.getElementById('ready-btn').addEventListener('click', function () {
        if (socket && user_id) {
            socket.emit(ClientMessageType.Ready);
        }
    });
    // 查看/修改房间设置按钮点击事件
    document.getElementById('edit-room-settings-btn').addEventListener('click', function () {
        if (socket && user_id) {
            // 如果是房主，可以修改设置
            if (is_owner && room_info && room_info.settings) {
                // 打开规则设置模态框前，先加载当前设置值
                document.getElementById('setting-235-greater').checked = room_info.settings.is_235_greater_than_three_of_a_kind;
                document.getElementById('setting-initial-coins').value = room_info.settings.initial_coins;
                document.getElementById('setting-base-bet').value = room_info.settings.base_bet;
                document.getElementById('setting-max-bet').value = room_info.settings.max_bet;
                document.getElementById('setting-max-hands').value = room_info.settings.max_hands;
                document.getElementById('setting-max-pot-amount').value = room_info.settings.max_pot_amount || 1000;

                // 打开规则设置模态框
                // 使用common.js中的函数显示模态框
    if (typeof showModal === 'function') {
        showModal('rules-settings-modal');
    } else {
        document.getElementById('rules-settings-modal').style.display = 'block';
    }
            } else {
                // 非房主，只能查看设置
                socket.emit(ClientMessageType.GetRoomDetails, { [ClientDataKey.RoomID]: currentRoomId });
            }
        } else {
            console.error('Socket未连接或用户未登录');
            alert('请先登录后再操作');
        }
    });

    // 保存设置按钮点击事件
    document.getElementById('save-settings-btn').addEventListener('click', function () {
        if (socket && user_id && is_owner) {
            const is_235_greater = document.getElementById('setting-235-greater').checked;
            const initial_coins = parseInt(document.getElementById('setting-initial-coins').value);
            const base_bet = parseInt(document.getElementById('setting-base-bet').value);
            const max_bet = parseInt(document.getElementById('setting-max-bet').value);
            const max_hands = parseInt(document.getElementById('setting-max-hands').value);
            const max_pot_amount = parseInt(document.getElementById('setting-max-pot-amount').value);

            socket.emit(ClientMessageType.UpdateRoomSettings, {
                [ClientDataKey.RoomID]: currentRoomId,
                [ClientDataKey.Settings]: {
                    '235_greater': is_235_greater,
                    initial_coins: initial_coins,
                    base_bet: base_bet,
                    max_bet: max_bet,
                    max_hands: max_hands,
                    max_pot_amount: max_pot_amount
                }
            });

            // 立即更新本地room_info对象中的设置值，确保房主界面上的数值立即更新
            if (room_info && room_info.settings) {
                room_info.settings.is_235_greater_than_three_of_a_kind = is_235_greater;
                room_info.settings.initial_coins = initial_coins;
                room_info.settings.base_bet = base_bet;
                room_info.settings.max_bet = max_bet;
                room_info.settings.max_hands = max_hands;
                room_info.settings.max_pot_amount = max_pot_amount;
            }

            // 直接更新查看房间设置模态框中的显示元素
            if (document.getElementById('view-setting-235-greater')) {
                document.getElementById('view-setting-235-greater').textContent = is_235_greater ? '是' : '否';
            }
            if (document.getElementById('view-setting-initial-coins')) {
                document.getElementById('view-setting-initial-coins').textContent = initial_coins;
            }
            if (document.getElementById('view-setting-base-bet')) {
                document.getElementById('view-setting-base-bet').textContent = base_bet;
            }
            if (document.getElementById('view-setting-max-bet')) {
                document.getElementById('view-setting-max-bet').textContent = max_bet ? max_bet : '无限制';
            }
            if (document.getElementById('view-setting-max-hands')) {
                document.getElementById('view-setting-max-hands').textContent = max_hands ? max_hands : '无限制';
            }
            if (document.getElementById('view-setting-max-pot-amount')) {
                document.getElementById('view-setting-max-pot-amount').textContent = max_pot_amount ? max_pot_amount : '无限制';
            }

            // 更新当前玩家的金币数显示，当初始金币数被修改时
            if (room_info && room_info.players && room_info.players[user_id]) {
                room_info.players[user_id].coins = initial_coins;
                document.getElementById('player-coins').textContent = `金币: ${initial_coins}`;
            }

            // 强制关闭设置面板并确保不会自动重新打开
            const rulesSettingsModal = document.getElementById('rules-settings-modal');
            rulesSettingsModal.classList.remove('show');
            rulesSettingsModal.style.display = 'none';
            setTimeout(() => {
                rulesSettingsModal.style.display = '';
            }, 100);

            // 禁用开始按钮5秒
            const startGameBtn = document.getElementById('start-game-btn');
            startGameBtn.disabled = true;
            startGameBtn.textContent = '5秒后可点击';

            let countdown = 5;
            const timer = setInterval(() => {
                countdown--;
                startGameBtn.textContent = `${countdown}秒后可点击`;
                if (countdown <= 0) {
                    clearInterval(timer);
                    startGameBtn.disabled = false;
                    startGameBtn.textContent = '开始游戏';

                    // 检查是否可以开始游戏（所有玩家都已准备且人数>=2）
                    const updateRoomInfoData = {
                        players: room_info ? room_info.players : {},
                        seats: room_info ? room_info.seats : [null, null, null, null, null, null],
                        owner: room_info ? room_info.owner : null,
                        settings: room_info ? room_info.settings : {},
                        ready_players: room_info ? room_info.ready_players : []
                    };
                    updateRoomInfo(updateRoomInfoData);
                }
            }, 1000);
        }
    });

    // 关闭规则设置面板按钮点击事件
    document.getElementById('close-settings-modal-btn').addEventListener('click', function () {
        // 使用common.js中的函数隐藏模态框
        if (typeof hideModal === 'function') {
            hideModal('rules-settings-modal');
        } else {
            // 强制关闭设置面板并确保不会自动重新打开
            const rulesSettingsModal = document.getElementById('rules-settings-modal');
            rulesSettingsModal.classList.remove('show');
            rulesSettingsModal.style.display = 'none';
            setTimeout(() => {
                rulesSettingsModal.style.display = '';
            }, 100);
        }
    });

    // 查看房间设置按钮点击事件
    document.getElementById('view-room-settings-btn').addEventListener('click', function () {
        console.log('查看房间设置按钮被点击');
        // 立即获取模态框元素
        const viewSettingsModal = document.getElementById('view-room-settings-modal');
        if (!viewSettingsModal) {
            console.error('未找到view-room-settings-modal模态框元素');
            return;
        }

        if (socket) {
            console.log('Socket连接存在');
            // 先检查用户是否在房间中
            console.log('user_id:', user_id);
            console.log('room_info:', room_info);
            console.log('room_info.players:', room_info ? room_info.players : 'undefined');
            if (user_id && room_info && room_info.players && room_info.players[user_id]) {
                console.log('用户在房间中，准备显示模态框并发送请求');

                // 先使用默认设置更新面板，确保即使服务器响应失败也能显示
                const viewSetting235Greater = document.getElementById('view-setting-235-greater');
                const viewSettingInitialCoins = document.getElementById('view-setting-initial-coins');
                const viewSettingBaseBet = document.getElementById('view-setting-base-bet');
                const viewSettingMaxBet = document.getElementById('view-setting-max-bet');
                const viewSettingMaxHands = document.getElementById('view-setting-max-hands');
                const viewSettingMaxPotAmount = document.getElementById('view-setting-max-pot-amount');

                if (viewSetting235Greater) viewSetting235Greater.textContent = '否';
                if (viewSettingInitialCoins) viewSettingInitialCoins.textContent = '1000';
                if (viewSettingBaseBet) viewSettingBaseBet.textContent = '1';
                if (viewSettingMaxBet) viewSettingMaxBet.textContent = '无限制';
                if (viewSettingMaxHands) viewSettingMaxHands.textContent = '无限制';
                if (viewSettingMaxPotAmount) viewSettingMaxPotAmount.textContent = '1000';

                // 记录当前状态
                console.log('修改前 - 类列表:', viewSettingsModal.classList.toString());
                console.log('修改前 - 计算样式display:', getComputedStyle(viewSettingsModal).display);

                // 强制显示模态框 - 多种方式确保显示
                viewSettingsModal.style.zIndex = '9999';
                viewSettingsModal.style.visibility = 'visible';
                viewSettingsModal.style.opacity = '1';
                viewSettingsModal.style.display = 'block';
                viewSettingsModal.classList.add('show');

                // 记录修改后的状态
                console.log('修改后 - 类列表:', viewSettingsModal.classList.toString());
                console.log('修改后 - 计算样式display:', getComputedStyle(viewSettingsModal).display);
                console.log('修改后 - 直接样式display:', viewSettingsModal.style.display);

                // 检查父元素的状态
                const parentElement = viewSettingsModal.parentElement;
                if (parentElement) {
                    console.log('父元素ID:', parentElement.id);
                    console.log('父元素计算样式display:', getComputedStyle(parentElement).display);
                }

                // 确保模态框内容区域可见
                const modalContent = viewSettingsModal.querySelector('.modal-content');
                if (modalContent) {
                    modalContent.style.display = 'block';
                    console.log('模态框内容区域display设置为block');
                }

                // 再次确认元素是否可见
                setTimeout(() => {
                    console.log('100ms后 - 计算样式display:', getComputedStyle(viewSettingsModal).display);
                    console.log('100ms后 - 是否包含show类:', viewSettingsModal.classList.contains('show'));
                    console.log('100ms后 - offsetWidth:', viewSettingsModal.offsetWidth);
                    console.log('100ms后 - offsetHeight:', viewSettingsModal.offsetHeight);
                }, 100);

                // 从服务器获取最新的房间设置
                try {
                    console.log('准备发送get_room_settings请求');
                    socket.emit(ClientMessageType.GetRoomDetails, { [ClientDataKey.RoomID]: currentRoomId });
                    console.log('get_room_settings请求已发送');
                } catch (error) {
                    console.error('发送get_room_settings请求时出错:', error);
                }
            } else {
                console.error('用户不在房间中');
                alert('您还没有加入房间，请先加入房间后再查看设置');
            }
        } else {
            console.error('Socket 未连接');
            alert('无法连接到服务器，请刷新页面重试');
        }
    });

    // 处理房间设置错误
    if (socket) {
        socket.on(ServerMessageType.RoomSettingsError, function (data) {
            console.error('获取房间设置错误:', data.error);
            console.log('当前用户ID:', user_id);
            console.log('前端房间信息:', room_info);
            console.log('前端房间玩家列表:', room_info ? Object.keys(room_info.players) : 'undefined');

            // 不使用alert，避免打断用户体验
            // 不立即关闭模态框，而是尝试使用默认设置显示
            const viewSettingsModal = document.getElementById('view-room-settings-modal');
            if (viewSettingsModal) {
                console.log('尝试使用默认设置显示房间设置面板');

                // 使用默认设置更新面板
                const viewSetting235Greater = document.getElementById('view-setting-235-greater');
                const viewSettingInitialCoins = document.getElementById('view-setting-initial-coins');
                const viewSettingBaseBet = document.getElementById('view-setting-base-bet');
                const viewSettingMaxBet = document.getElementById('view-setting-max-bet');
                const viewSettingMaxHands = document.getElementById('view-setting-max-hands');
                const viewSettingMaxPotAmount = document.getElementById('view-setting-max-pot-amount');

                if (viewSetting235Greater) viewSetting235Greater.textContent = '否';
                if (viewSettingInitialCoins) viewSettingInitialCoins.textContent = '1000';
                if (viewSettingBaseBet) viewSettingBaseBet.textContent = '1';
                if (viewSettingMaxBet) viewSettingMaxBet.textContent = '无限制';
                if (viewSettingMaxHands) viewSettingMaxHands.textContent = '无限制';
                if (viewSettingMaxPotAmount) viewSettingMaxPotAmount.textContent = '1000';

                // 确保模态框显示
                viewSettingsModal.classList.add('show');
                console.log('模态框显示状态:', viewSettingsModal.classList.contains('show'));
            }
        });
    }

    // 关闭查看房间设置模态框按钮点击事件
    document.getElementById('close-view-settings-modal-btn').addEventListener('click', function () {
        const viewSettingsModal = document.getElementById('view-room-settings-modal');
        // 移除show类
        viewSettingsModal.classList.remove('show');
        // 同时重置display样式，确保覆盖之前直接设置的display:block
        viewSettingsModal.style.display = 'none';
        console.log('关闭模态框后 - 类列表:', viewSettingsModal.classList.toString());
        console.log('关闭模态框后 - 直接样式display:', viewSettingsModal.style.display);
    });

    // 关闭规则设置结果面板按钮点击事件
    document.getElementById('close-settings-update-modal-btn').addEventListener('click', function () {
    // 使用common.js中的函数隐藏模态框
    if (typeof hideModal === 'function') {
        hideModal('settings-update-modal');
    } else {
        document.getElementById('settings-update-modal').classList.remove('show');
    }
});

    // 踢出玩家按钮点击事件
    document.getElementById('kick-player-btn').addEventListener('click', function () {
        if (socket && user_id && is_owner) {
            const player_to_kick = document.getElementById('kick-player-select').value;
            if (player_to_kick) {
                socket.emit(ClientMessageType.KickPlayer, {
                    [ClientDataKey.RoomID]: currentRoomId,
                    [ClientDataKey.PlayerIdToBeKicked]: player_to_kick
                });
            }
        }
    });

    // 开始游戏按钮点击事件
    document.getElementById('start-game-btn').addEventListener('click', function () {
        if (socket && user_id && is_owner) {
            // 发送ready事件，由服务器处理游戏开始逻辑
            socket.emit(ClientMessageType.Ready);
        }
    });

    // 为每个座位添加点击事件
    for (let i = 0; i < 6; i++) {
        const seat = document.querySelector(`.seat-${i}`);
        seat.addEventListener('click', function () {
            if (socket && user_id && window.visualPos2SeatNumMap) {
                // 直接使用全局映射找到实际座位号
                const actualSeatIndex = window.visualPos2SeatNumMap[i];
                socket.emit(ClientMessageType.SitDown, {
                    [ClientDataKey.SeatIndex]: actualSeatIndex
                });
            }
        });
    }
});

// Socket.IO重试连接计数器
let socketConnectAttempts = 0;
const maxConnectAttempts = 3;

// 连接SocketIO
function connectSocket() {
    // 优先使用common.js中的函数初始化Socket连接
    if (typeof initSocketConnection === 'function') {
        console.log('使用common.js中的函数初始化Socket连接');
        socket = initSocketConnection({
            onUserIdAssigned: function(data) {
                user_id = data.user_id;
                console.log('收到服务器分配的user_id:', user_id);
                
                // 在收到user_id后再进行后续操作
                // 发送用户名
                if (username) {
                    socket.emit(ClientMessageType.SetUserInfo, { [ClientDataKey.Username]: username });
                }
                
                // 如果有房间ID，尝试重新获取房间信息
                if (currentRoomId) {
                    console.log('重新获取房间信息');
                    socket.emit(ClientMessageType.GetRoomDetails, { [ClientDataKey.RoomID]: currentRoomId });
                }
                
                // 更新用户显示
                if (typeof updateUserDisplay === 'function') {
                    updateUserDisplay();
                }
            }
        });
        
        // 设置基本的Socket事件监听
        if (typeof setupBasicSocketListeners === 'function' && socket) {
            setupBasicSocketListeners(socket, {
                onUsernameError: function(data) {
                    console.log('用户名错误:', data);
                    alert(`用户名错误: ${data.message}`);
                },
                customConnectedHandler: function(data) {
                    console.log('收到服务器连接确认:', data);
                    
                    // 使用common.js中的函数处理重连逻辑
                    attemptReconnectWithSavedId(socket);
                }
            });
            
            // 设置其他特定的Socket事件监听
            setupCustomSocketListeners();
        } else if (socket) {
            // 如果common.js中的函数不可用，使用原有的setupSocketListeners
            setupSocketListeners();
        }
    } else {
        // 如果common.js中的函数不可用，使用原有的连接逻辑
        // 确保io对象已加载，然后创建SocketIO连接
        if (typeof io !== 'undefined') {
            console.log('Socket.IO客户端库已加载，尝试连接服务器');
            // 明确指定连接URL，使用当前页面的主机和端口
            const socketUrl = window.location.protocol + '//' + window.location.host;

            // 配置连接选项
            const ioOptions = {
                transports: ['websocket', 'polling'], // 优先使用websocket，降级到polling
                timeout: 5000,
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            };

            socket = io(socketUrl, ioOptions);
            setupSocketListeners();
        } else {
            socketConnectAttempts++;
            console.error('Socket.IO 客户端库未加载成功，尝试次数:', socketConnectAttempts);

            if (socketConnectAttempts <= maxConnectAttempts) {
                // 重试连接
                setTimeout(() => {
                    console.log('尝试重新连接...');
                    connectSocket();
                }, 2000);
            } else {
                // 尝试次数过多，显示错误提示
                alert('Socket.IO客户端库加载失败，请检查网络连接后刷新页面重试');
                console.log('已尝试最大连接次数，停止重试');
            }
            return; // 添加return防止继续执行
        }
    }
}

// 更新房间列表
function updateRoomList(rooms) {
    const roomListContainer = document.getElementById('room-list-container');
    const noRoomsMessage = document.getElementById('no-rooms-message');
    
    // 清空当前房间列表
    roomListContainer.innerHTML = '';
    
    if (rooms.length === 0) {
        // 显示无房间消息
        noRoomsMessage.style.display = 'block';
    } else {
        // 隐藏无房间消息
        noRoomsMessage.style.display = 'none';
        
        // 创建房间列表表格
        const table = document.createElement('table');
        table.className = 'table table-striped';
        
        // 创建表头
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th>房间名称</th>
            <th>玩家数量</th>
            <th>状态</th>
            <th>操作</th>
        `;
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // 创建表体
        const tbody = document.createElement('tbody');
        
        // 添加每个房间到列表
        rooms.forEach(room => {
            const row = document.createElement('tr');
            const statusClass = room.status === 'waiting' ? 'room-status-waiting' : 'room-status-playing';
            const statusText = room.status === 'waiting' ? '等待中' : '游戏中';
            const isFull = room.player_count >= room.max_players;
            const isPlaying = room.status === 'playing';
            
            row.innerHTML = `
                <td>${room.room_name}</td>
                <td>${room.player_count}/${room.max_players}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <button class="btn-join-room" 
                            onclick="joinRoom('${room.room_id}')" 
                            ${isFull || isPlaying ? 'disabled' : ''}>
                        ${isFull ? '已满' : (isPlaying ? '游戏中' : '加入')}
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        roomListContainer.appendChild(table);
    }
}

// 加入房间
function joinRoom(roomId) {
    socket.emit(ClientMessageType.JoinRoom, {
        [ClientDataKey.RoomID]: roomId
    });
}

// 筛选房间
function filterRooms() {
    const statusFilter = document.getElementById('status-filter').value;
    const nameFilter = document.getElementById('name-filter').value.toLowerCase();
    
    // 获取所有房间行
    const rows = document.querySelectorAll('#room-list-container tbody tr');
    
    rows.forEach(row => {
        const nameCell = row.cells[0].textContent.toLowerCase();
        const statusCell = row.cells[2].textContent;
        
        // 检查是否匹配筛选条件
        const nameMatch = nameFilter === '' || nameCell.includes(nameFilter);
        const statusMatch = statusFilter === 'all' || 
                            (statusFilter === 'waiting' && statusCell === '等待中') || 
                            (statusFilter === 'playing' && statusCell === '游戏中');
        
        // 显示或隐藏行
        row.style.display = nameMatch && statusMatch ? '' : 'none';
    });
}

// 重置筛选
function resetFilters() {
    document.getElementById('status-filter').value = 'all';
    document.getElementById('name-filter').value = '';
    filterRooms();
}

// 刷新房间列表
function refreshRoomList() {
    socket.emit(ClientMessageType.GetRoomList);
}

// 切换私有房间密码输入
function togglePrivatePassword() {
    const isPrivateCheckbox = document.getElementById('is-private');
    const passwordContainer = document.getElementById('password-container');
    
    if (isPrivateCheckbox.checked) {
        passwordContainer.style.display = 'block';
    } else {
        passwordContainer.style.display = 'none';
    }
}

// 初始化房间列表相关的事件监听器
function initRoomListEvents() {
    // 添加房间列表按钮点击事件
    const roomListBtn = document.getElementById('room-list-btn');
    if (roomListBtn) {
        roomListBtn.addEventListener('click', function () {
            document.getElementById('room-list-modal').classList.add('show');
            // 获取房间列表
            socket.emit(ClientMessageType.GetRoomList);
        });
    }

    // 添加创建房间按钮点击事件
    const createRoomBtn = document.getElementById('create-room-btn');
    if (createRoomBtn) {
        createRoomBtn.addEventListener('click', function () {
            document.getElementById('create-room-modal').classList.add('show');
        });
    }

    // 添加关闭房间列表模态框按钮点击事件
    const closeRoomListModalBtn = document.getElementById('close-room-list-modal-btn');
    if (closeRoomListModalBtn) {
        closeRoomListModalBtn.addEventListener('click', function () {
            document.getElementById('room-list-modal').classList.remove('show');
        });
    }

    // 添加关闭创建房间模态框按钮点击事件
    const closeCreateRoomModalBtn = document.getElementById('close-create-room-modal-btn');
    if (closeCreateRoomModalBtn) {
        closeCreateRoomModalBtn.addEventListener('click', function () {
            document.getElementById('create-room-modal').classList.remove('show');
        });
    }

    // 添加创建房间表单提交事件
    const createRoomForm = document.getElementById('create-room-form');
    if (createRoomForm) {
        createRoomForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const roomName = document.getElementById('room-name').value;
            const maxPlayers = parseInt(document.getElementById('max-players').value);
            const isPrivate = document.getElementById('is-private').checked;
            const roomPassword = document.getElementById('room-password').value;
            const initialCoins = parseInt(document.getElementById('initial-coins').value);
            const baseBet = parseInt(document.getElementById('base-bet').value);
            const maxBet = document.getElementById('max-bet').value ? parseInt(document.getElementById('max-bet').value) : null;
            const maxHands = document.getElementById('max-hands').value ? parseInt(document.getElementById('max-hands').value) : null;
            const is235Greater = document.getElementById('is-235-greater').checked;

            // 创建房间
            socket.emit(ClientMessageType.CreateRoom, {
                [ClientDataKey.RoomName]: roomName,
                max_players: maxPlayers,
                is_private: isPrivate,
                room_password: roomPassword,
                [ClientDataKey.Settings]: {
                    initial_coins: initialCoins,
                    base_bet: baseBet,
                    max_bet: maxBet,
                    max_hands: maxHands,
                    is_235_greater_than_three_of_a_kind: is235Greater
                }
            });

            // 使用common.js中的函数隐藏模态框
            if (typeof hideModal === 'function') {
                hideModal('create-room-modal');
            } else {
                document.getElementById('create-room-modal').classList.remove('show');
            }
        });
    }
}

// 初始化页面
function initializePage() {
    // 添加私有房间复选框事件监听器
    const isPrivateCheckbox = document.getElementById('is-private');
    if (isPrivateCheckbox) {
        isPrivateCheckbox.addEventListener('change', togglePrivatePassword);
    }
    
    // 初始时隐藏密码输入框
    togglePrivatePassword();
    
    // 尝试获取保存的用户信息
    if (typeof getCurrentUser === 'function') {
        const savedUser = getCurrentUser();
        if (savedUser) {
            // 如果有保存的用户名，设置到全局变量
            if (savedUser.username) {
                username = savedUser.username;
            }
            // 如果有保存的头像，设置到全局变量
            if (savedUser.avatar_url) {
                selectedAvatarUrl = savedUser.avatar_url;
                avatarSelected = true;
                // 更新头像预览
                const avatarPreview = document.getElementById('avatar-preview');
                if (avatarPreview) {
                    avatarPreview.src = savedUser.avatar_url;
                }
            }
        }
    }
}

// 更新用户显示
function updateUserDisplay() {
    // 优先使用common.js中的函数更新用户显示
    if (typeof updateUserDisplayFromCommon === 'function') {
        updateUserDisplayFromCommon();
    } else if (typeof getCurrentUser === 'function') {
        // 如果common.js中的函数不可用，使用降级方案
        const currentUser = getCurrentUser();
        if (currentUser) {
            // 更新页面上的用户信息显示
            if (currentUser.username && document.getElementById('player-name')) {
                document.getElementById('player-name').textContent = `玩家昵称：${currentUser.username}`;
            }
            // 更新头像显示
            if (currentUser.avatar_url && document.getElementById('user-avatar')) {
                document.getElementById('user-avatar').src = currentUser.avatar_url;
            }
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initializePage();
    
    // 尝试使用common.js中的函数初始化Socket连接
    if (typeof initSocketConnection === 'function') {
        socket = initSocketConnection();
    }
    
    // 设置基本的Socket事件监听
    if (typeof setupBasicSocketListeners === 'function' && socket) {
        setupBasicSocketListeners(socket);
    } else if (socket) {
        // 如果common.js中的函数不可用，使用原有的setupSocketListeners
        setupSocketListeners();
    }
});

// 更新房间信息
function updateRoomInfo(data) {
    // 这里是原有的更新房间信息函数
    // 保持原有代码不变
}

// 开始游戏
function startGame(data) {
    // 这里是原有的开始游戏函数
    // 保持原有代码不变
}

// 设置SocketIO事件监听器
function setupSocketListeners() {
    // 优先使用common.js中的函数设置基本的Socket事件监听
    if (typeof setupBasicSocketListeners === 'function' && socket) {
        setupBasicSocketListeners(socket, {
            onConnect: function() {
                console.log('连接成功');
                
                // 使用common.js中的函数获取用户ID
                const savedUserId = getUserId();
                
                // 如果有保存的user_id，发送给服务器用于重连识别
                if (savedUserId) {
                    console.log('使用保存的user_id进行重连:', savedUserId);
                    socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: savedUserId });
                }

                // 发送用户名
                socket.emit(ClientMessageType.SetUserInfo, {
                    [ClientDataKey.Username]: username
                });

                // 首次设置时，如果已选择头像，立即设置头像
                if (avatarSelected && selectedAvatarUrl) {
                    // 使用common.js中的函数处理头像URL
                    if (typeof getCleanAvatarUrl === 'function') {
                        const cleanAvatarUrl = getCleanAvatarUrl(selectedAvatarUrl);
                        socket.emit(ClientMessageType.SetAvatar, { [ClientDataKey.AvatarURL]: cleanAvatarUrl });
                    } else {
                        // 降级方案 - 如果common.js中的函数不可用
                        let cleanAvatarUrl = selectedAvatarUrl;
                        if (selectedAvatarUrl.includes('?')) {
                            const urlParts = selectedAvatarUrl.split('?');
                            const queryParams = new URLSearchParams(urlParts[1]);
                            queryParams.delete('t');
                            cleanAvatarUrl = urlParts[0];
                            if (queryParams.toString()) {
                                cleanAvatarUrl += '?' + queryParams.toString();
                            }
                        }
                        socket.emit(ClientMessageType.SetAvatar, { [ClientDataKey.AvatarURL]: cleanAvatarUrl });
                    }
                }
                
                // 初始化房间列表相关的事件监听器
                initRoomListEvents();
                
                // 获取房间列表
                socket.emit(ClientMessageType.GetRoomList);
            },
            onUsernameError: function(data) {
                console.log('用户名错误:', data);
                // 房间页面不显示用户设置模态框，直接提示错误
                alert(data.error || data.message || '用户名错误');
            },
            customConnectedHandler: function(data) {
                console.log('收到服务器连接确认:', data);
            }
        });
        
        // 设置其他特定的Socket事件监听
        setupCustomSocketListeners();
    } else if (socket) {
        // 如果common.js中的函数不可用，使用原有的连接逻辑
        // 连接成功
        socket.on('connect', function () {
            console.log('连接成功');
            user_id = socket.id;
            
            // 使用common.js中的函数获取用户ID
            const savedUserId = getUserId();
            
            // 如果有保存的user_id，发送给服务器用于重连识别
            if (savedUserId) {
                console.log('使用保存的user_id进行重连:', savedUserId);
                socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: savedUserId });
            }

            // 发送用户名
            socket.emit(ClientMessageType.SetUserInfo, {
                [ClientDataKey.Username]: username
            });

            // 首次设置时，如果已选择头像，立即设置头像
            if (avatarSelected && selectedAvatarUrl) {
                // 移除已有的时间戳参数，避免重复添加
                let cleanAvatarUrl = selectedAvatarUrl;
                if (selectedAvatarUrl.includes('?')) {
                    const urlParts = selectedAvatarUrl.split('?');
                    const queryParams = new URLSearchParams(urlParts[1]);
                    queryParams.delete('t');
                    cleanAvatarUrl = urlParts[0];
                    if (queryParams.toString()) {
                        cleanAvatarUrl += '?' + queryParams.toString();
                    }
                }

                // 添加新的时间戳防止浏览器缓存
                const timestamp = new Date().getTime();
                const avatarUrlWithTimestamp = cleanAvatarUrl.includes('?')
                    ? `${cleanAvatarUrl}&t=${timestamp}`
                    : `${cleanAvatarUrl}?t=${timestamp}`;

                // 发送头像设置请求
                socket.emit(ClientMessageType.SetAvatar, { [ClientDataKey.AvatarURL]: avatarUrlWithTimestamp });
            }
            
            // 初始化房间列表相关的事件监听器
            initRoomListEvents();
            
            // 获取房间列表
            socket.emit(ClientMessageType.GetRoomList);
        });
    
        // 接收服务器分配的user_id并存储
        socket.on(ServerMessageType.UserIDAssigned, function(data) {
            const user_id = data.user_id;
            console.log('收到服务器分配的user_id:', user_id);
            // 使用common.js中的函数保存用户ID
            saveUserId(user_id);
        });
    }
}

// 设置房间相关的自定义Socket事件监听器
function setupCustomSocketListeners() {
    if (!socket) return;

    // 接收设置更新通知
    socket.on(ServerMessageType.SettingsUpdated, function (data) {
        // 显示规则设置结果面板
        const settingsUpdateModal = document.getElementById('settings-update-modal');

        // 更新消息
        document.getElementById('settings-update-message').textContent = `房主更改了房间设置：${data.message}`;

        // 如果有房间信息，更新设置显示
        if (data.room_info && data.room_info.settings) {
            const settings = data.room_info.settings;
            document.getElementById('update-setting-235-greater').textContent = settings.is_235_greater_than_three_of_a_kind ? '是' : '否';
            document.getElementById('update-setting-initial-coins').textContent = settings.initial_coins || 1000;
            document.getElementById('update-setting-base-bet').textContent = settings.base_bet || 1;
        }
    });

    // 接收设置更新通知
    socket.on(ServerMessageType.SettingsUpdated, function (data) {
        // 显示规则设置结果面板
        const settingsUpdateModal = document.getElementById('settings-update-modal');

        // 更新消息
        document.getElementById('settings-update-message').textContent = `房主更改了房间设置：${data.message}`;

        // 如果有房间信息，更新设置显示
        if (data.room_info && data.room_info.settings) {
            const settings = data.room_info.settings;
            document.getElementById('update-setting-235-greater').textContent = settings.is_235_greater_than_three_of_a_kind ? '是' : '否';
            document.getElementById('update-setting-initial-coins').textContent = settings.initial_coins || 1000;
            document.getElementById('update-setting-base-bet').textContent = settings.base_bet || 1;
            document.getElementById('update-setting-max-bet').textContent = settings.max_bet ? settings.max_bet : '无限制';
            document.getElementById('update-setting-max-hands').textContent = settings.max_hands ? settings.max_hands : '无限制';
        }

        // 显示面板
        settingsUpdateModal.classList.add('show');

        // 重新更新房间信息
        if (data.room_info) {
            updateRoomInfo(data.room_info);
        }

        // 如果玩家已准备，取消准备状态
        if (is_ready) {
            is_ready = false;
            if (document.getElementById('ready-btn')) {
                document.getElementById('ready-btn').textContent = '准备就绪';
            }
        }
    });

    // 接收房间设置数据
    socket.on(ServerMessageType.RoomSettings, function (data) {
        console.log('接收到房间设置数据:', data);

        // 强制更新设置数据到模态框中
        const viewSetting235Greater = document.getElementById('view-setting-235-greater');
        const viewSettingInitialCoins = document.getElementById('view-setting-initial-coins');
        const viewSettingBaseBet = document.getElementById('view-setting-base-bet');
        const viewSettingMaxBet = document.getElementById('view-setting-max-bet');
        const viewSettingMaxHands = document.getElementById('view-setting-max-hands');

        if (viewSetting235Greater) {
            console.log('更新235大于豹子设置:', data.is_235_greater_than_three_of_a_kind);
            viewSetting235Greater.textContent = data.is_235_greater_than_three_of_a_kind ? '是' : '否';
        } else {
            console.log('未找到view-setting-235-greater元素');
        }
        if (viewSettingInitialCoins) {
            console.log('更新初始金币数:', data.initial_coins);
            viewSettingInitialCoins.textContent = data.initial_coins || 1000;
        } else {
            console.log('未找到view-setting-initial-coins元素');
        }
        if (viewSettingBaseBet) {
            console.log('更新底注数量:', data.base_bet);
            viewSettingBaseBet.textContent = data.base_bet || 1;
        } else {
            console.log('未找到view-setting-base-bet元素');
        }
        if (viewSettingMaxBet) {
            console.log('更新最大下注:', data.max_bet);
            viewSettingMaxBet.textContent = data.max_bet ? data.max_bet : '无限制';
        } else {
            console.log('未找到view-setting-max-bet元素');
        }
        if (viewSettingMaxHands) {
            console.log('更新最大局数:', data.max_hands);
            viewSettingMaxHands.textContent = data.max_hands ? data.max_hands : '无限制';
        } else {
            console.log('未找到view-setting-max-hands元素');
        }

        // 强制显示查看房间设置模态框
        const viewRoomSettingsModal = document.getElementById('view-room-settings-modal');
        if (viewRoomSettingsModal) {
            console.log('找到view-room-settings-modal模态框，开始强制显示逻辑');

            // 记录当前状态
            console.log('修改前 - 类列表:', viewRoomSettingsModal.classList.toString());
            console.log('修改前 - 计算样式display:', getComputedStyle(viewRoomSettingsModal).display);
            console.log('修改前 - 直接样式display:', viewRoomSettingsModal.style.display);

            // 确保没有其他元素影响这个元素的显示
            viewRoomSettingsModal.style.zIndex = '9999';
            viewRoomSettingsModal.style.visibility = 'visible';
            viewRoomSettingsModal.style.opacity = '1';

            // 直接设置display属性以确保显示
            viewRoomSettingsModal.style.display = 'block';

            // 同时也添加show类以符合现有的CSS逻辑
            viewRoomSettingsModal.classList.add('show');

            // 记录修改后的状态
            console.log('修改后 - 类列表:', viewRoomSettingsModal.classList.toString());
            console.log('修改后 - 计算样式display:', getComputedStyle(viewRoomSettingsModal).display);
            console.log('修改后 - 直接样式display:', viewRoomSettingsModal.style.display);

            // 检查父元素的状态
            const parentElement = viewRoomSettingsModal.parentElement;
            if (parentElement) {
                console.log('父元素ID:', parentElement.id);
                console.log('父元素计算样式display:', getComputedStyle(parentElement).display);
            }

            // 再次确认元素是否可见
            setTimeout(() => {
                console.log('100ms后 - 计算样式display:', getComputedStyle(viewRoomSettingsModal).display);
                console.log('100ms后 - 是否包含show类:', viewRoomSettingsModal.classList.contains('show'));
                console.log('100ms后 - offsetWidth:', viewRoomSettingsModal.offsetWidth);
                console.log('100ms后 - offsetHeight:', viewRoomSettingsModal.offsetHeight);
            }, 100);
        } else {
            console.log('未找到view-room-settings-modal模态框');
        }
    });

    // 接收房间列表数据
    socket.on(ServerMessageType.RoomList, function (data) {
        console.log('接收到房间列表数据:', data);
        updateRoomList(data.rooms);
    });

    // 接收创建房间响应
    socket.on(ServerMessageType.RoomCreated, function (data) {
        console.log('房间创建成功:', data);
        // 关闭房间列表模态框
        document.getElementById('room-list-modal').classList.remove('show');
        // 刷新房间列表
        socket.emit(ClientMessageType.GetRoomList);
    });

    // 接收加入房间响应
    socket.on(ServerMessageType.RoomJoined, function (data) {
        console.log('加入房间成功:', data);
        // 保存房间ID到全局变量
        currentRoomId = data.room_id;
        console.log('保存的房间ID:', currentRoomId);
        // 关闭房间列表模态框
        document.getElementById('room-list-modal').classList.remove('show');
    });

    // 接收房间错误信息
    socket.on(ServerMessageType.RoomError, function (data) {
        console.error('房间操作错误:', data);
        alert('房间操作失败: ' + data.error);
    });

    // 连接断开
    socket.on('disconnect', function () {
        console.log('连接断开');
    });
    
    // 接收用户信息更新通知
    socket.on(ServerMessageType.UserInfoUpdated, function(data) {
        console.log('用户信息已更新:', data);
        // 确保数据格式与我们的期望一致
        const user = {
            username: data.user.username,
            avatar_url: data.user.avatar || data.user.avatar_url,
            coins: data.user.coins || 0,
            user_id: data.user.user_id
        };
        
        // 使用common.js中的函数保存用户信息
        if (typeof saveCurrentUser === 'function') {
            saveCurrentUser(user);
        }
    });

    // 接收房间更新
    socket.on(ServerMessageType.RoomUpdated, function (data) {
        updateRoomInfo(data);
    });

    // 接收游戏开始
    socket.on(ServerMessageType.GameStart, function (data) {
        startGame(data);
    });

    // 接收回合开始
    socket.on(ServerMessageType.StartTurn, function (data) {
        console.log('回合开始', data);
        document.getElementById('game-status').textContent = `现在是 ${data.player_name} 的回合`;

        // 高亮当前玩家的座位
        document.querySelectorAll('.seat').forEach(seat => {
            seat.classList.remove('current-turn');
        });

        for (let i = 0; i < 6; i++) {
            if (room_info && room_info.seats[i] === data.player_id) {
                const currentSeat = document.querySelector(`.seat-${i}`);
                if (currentSeat) {
                    currentSeat.classList.add('current-turn');
                }
                break;
            }
        }

        // 检查是否只剩两个活跃玩家，如果是，显示开牌按钮
        if (data.active_players_count === 2) {
            document.getElementById('showdown-btn').style.display = 'block';
            // 添加脉冲动画效果
            document.getElementById('showdown-btn').classList.add('showdown-available');
        } else {
            document.getElementById('showdown-btn').style.display = 'none';
            // 移除脉冲动画效果
            document.getElementById('showdown-btn').classList.remove('showdown-available');
        }
    });

    // 接收玩家看牌
    socket.on(ServerMessageType.ShowCards, function (data) {
        console.log('玩家看牌', data);
        if (data.player_id === user_id) {
            // 显示自己的手牌
            const hand = data.hand;
            let handHtml = '<div class="player-hand">';
            hand.forEach(card => {
                // 确定花色并添加对应的颜色类
                let suit = card[0];
                let rank = card[1];
                let colorClass = '';
                
                // 红色花色：♥️♦️
                if (suit === '♥️' || suit === '♦️') {
                    colorClass = 'card-red';
                } 
                // 黑色花色：♠️♣️
                else if (suit === '♠️' || suit === '♣️') {
                    colorClass = 'card-black';
                }
                
                handHtml += `<div class="game-card ${colorClass}">${suit}${rank}</div>`;
            });
            handHtml += '</div>';
            
            // 找到当前玩家的座位
            for (let i = 0; i < 6; i++) {
                if (room_info && room_info.seats[i] === user_id) {
                    // 使用视觉位置映射
                    const visualPos = window.seatNum2VisualPosMap[i];
                    const seat = document.querySelector(`.seat-${visualPos}`);
                    const playerInfo = seat.querySelector('.player-info');
                    
                    if (playerInfo) {
                        // 移除之前的手牌显示
                        const oldHand = playerInfo.querySelector('.player-hand');
                        if (oldHand) {
                            oldHand.remove();
                        }
                        
                        // 添加新手牌显示
                        playerInfo.insertAdjacentHTML('beforeend', handHtml);
                    }
                    break;
                }
            }
            
            alert('您已查看手牌！后续下注金额将翻倍。');
        }
    });

    // 接收玩家看牌通知
    socket.on(ServerMessageType.PlayerLookedCards, function (data) {
        console.log('玩家看牌通知', data);
        if (data.player_id !== user_id) {
            alert(`${data.player_name} 查看了手牌！`);
        }
    });

    // 接收玩家弃牌
    socket.on(ServerMessageType.PlayerFolded, function (data) {
        console.log('玩家弃牌', data);
        alert(`${data.player_name} 弃牌了！`);

        // 更新玩家状态
        updateRoomInfo(room_info);
    });

    // 接收玩家跟注
    socket.on(ServerMessageType.PlayerCalled, function (data) {
        console.log('玩家跟注', data);
        
        // 如果是当前玩家跟注，显示更详细的信息
        if (data.player_id === user_id) {
            // 检查玩家是否看牌
            let lookedCards = false;
            if (room_info && room_info.game_data && room_info.game_data.looked_cards) {
                // looked_cards是set类型，需要转换为数组或使用has方法
                // 这里我们将其转换为数组以便使用includes方法
                const lookedCardsArray = Array.isArray(room_info.game_data.looked_cards) 
                    ? room_info.game_data.looked_cards 
                    : Array.from(room_info.game_data.looked_cards || []);
                lookedCards = lookedCardsArray.includes(user_id);
            }
            
            // 根据是否看牌显示不同的提示信息
            if (lookedCards) {
                alert(`您跟注了 ${data.amount} 金币（看牌后下注翻倍）！`);
            } else {
                alert(`您跟注了 ${data.amount} 金币！`);
            }
        } else {
            alert(`${data.player_name} 跟注了 ${data.amount} 金币！`);
        }

        // 更新底池和玩家下注信息
        document.getElementById('pot-info').textContent = `当前底池: ${data.pot} 金币`;
        updateRoomInfo(room_info);
    });

    // 接收玩家加注
    socket.on(ServerMessageType.PlayerRaised, function (data) {
        console.log('玩家加注', data);
        alert(`${data.player_name} 加注了 ${data.amount} 金币！`);

        // 更新底池和当前下注金额
        document.getElementById('pot-info').textContent = `当前底池: ${data.pot} 金币`;
        document.getElementById('current-bet-info').textContent = `当前下注: ${data.current_bet} 金币`;
        updateRoomInfo(room_info);
    });

    // 接收无效加注提示
    socket.on(ServerMessageType.InvalidRaise, function (data) {
        console.log('无效加注', data);
        if (data.player_id === user_id) {
            alert(`加注金额无效！最小加注金额为 ${data.min_raise} 金币`);
        }
    });

    // 接收超过最大下注提示
    socket.on(ServerMessageType.ExceedMaxBet, function (data) {
        console.log('超过最大下注', data);
        if (data.player_id === user_id) {
            alert(`加注金额超过最大限制！最大下注金额为 ${data.max_bet} 金币`);
        }
    });

    // 接收金币不足提示
    socket.on(ServerMessageType.NotEnoughCoins, function (data) {
        console.log('金币不足', data);
        if (data.player_id === user_id) {
            alert('您的金币不足！');
        }
    });

    // 接收无效开牌提示
    socket.on(ServerMessageType.InvalidShowdown, function (data) {
        console.log('无效开牌', data);
        alert(data.message);
    });

    // 接收玩家请求开牌信息
    socket.on(ServerMessageType.PlayerRequestedShowdown, function (data) {
        console.log(`${data.player_name} 请求开牌`);
        // 可以在这里添加提示信息或动画效果
    });

    // 接收底池封顶事件
    socket.on(ServerMessageType.PotCapReached, function (data) {
        console.log('底池已达到上限', data);
        alert(`底池已达到上限！当前底池: ${data.current_pot}金币，最大底池: ${data.max_pot}金币。系统将自动开牌！`);
    });

    // 游戏结束时的处理
    socket.on(ServerMessageType.GameOver, function (data) {
        console.log('游戏结束！胜利者是:', data.winner_name);
        document.getElementById('game-status').textContent = '等待游戏开始...';

        // 显示获胜消息和继续游戏选项
        document.getElementById('winner-message').textContent = `恭喜玩家${data.winner_name}获胜！赢得了${data.pot}金币！`;

        // 显示所有玩家的手牌
        if (data.all_hands) {
            // 为每个玩家显示手牌
            for (const player_id in data.all_hands) {
                const player_hand_data = data.all_hands[player_id];

                // 找到该玩家的座位
                for (let i = 0; i < 6; i++) {
                    if (room_info && room_info.seats[i] === player_id) {
                        // 使用视觉位置映射
                        const visualPos = window.seatNum2VisualPosMap[i];
                        const seat = document.querySelector(`.seat-${visualPos}`);
                        const playerInfo = seat.querySelector('.player-info');

                        if (playerInfo) {
                            // 移除之前的手牌显示
                            const oldHand = playerInfo.querySelector('.player-hand');
                            if (oldHand) {
                                oldHand.remove();
                            }

                            // 如果玩家没有弃牌，显示手牌
                            if (!player_hand_data.is_folded) {
                                let handHtml = '<div class="player-hand">';
                                player_hand_data.hand.forEach(card => {
                                    handHtml += `<div class="game-card">${card[0]}${card[1]}</div>`;
                                });
                                handHtml += '</div>';

                                playerInfo.insertAdjacentHTML('beforeend', handHtml);
                            } else {
                                // 如果玩家弃牌，显示弃牌标记
                                playerInfo.insertAdjacentHTML('beforeend', '<div class="folded-mark">已弃牌</div>');
                            }
                        }
                        break;
                    }
                }
            }
        }

        // 显示继续游戏模态框
        document.getElementById('continue-modal').classList.add('show');

        // 隐藏游戏控制面板
        document.getElementById('game-controls').style.display = 'none';

        // 移除当前回合高亮
        document.querySelectorAll('.seat').forEach(seat => {
            seat.classList.remove('current-turn');
        });
    });

    // 继续游戏准备
    socket.on(ServerMessageType.ContinueGameReady, function (data) {
        console.log('准备继续游戏的玩家:', data.players_continue);
        alert('游戏准备开始，请各位玩家做好准备！');
    });

    // 游戏结束（玩家不足）
    socket.on(ServerMessageType.GameEnded, function (data) {
        console.log('游戏结束:', data.reason);
        alert(`游戏结束: ${data.reason}`);
    });
}

// 更新房间信息
/**
 * @function updateRoomInfo
 * @description 更新房间信息和玩家座位显示
 * @param {Object} data - 房间数据对象
 * @property {Array<string|null>} data.seats - 座位数组，长度为6，每个元素是玩家ID或null
 * @property {Object} data.players - 玩家对象，键是玩家ID，值是玩家信息对象
 * @property {string} data.owner - 房间所有者的玩家ID
 * @property {Array<string>} data.ready_players - 已准备玩家的ID数组
 * @property {Object} data.settings - 游戏设置对象
 */
function updateRoomInfo(data) {
    // 保存房间信息到全局变量，供其他函数访问
    room_info = data;

    // 检查是否需要重新计算座位显示位置
    // 只有在以下情况才重新计算：
    // 1. 全局映射尚未初始化
    // 2. 当前玩家的座位发生变化
    let needsRecalculatePositions = false;

    // 初始化全局变量（如果尚未初始化）
    if (!window.seatNum2VisualPosMap) {
        window.seatNum2VisualPosMap = new Array(6);
        needsRecalculatePositions = true;
    }

    // 查找当前玩家的座位索引
    let currentPlayerSeatIndex = -1;
    for (let i = 0; i < 6; i++) {
        if (data.seats[i] === user_id) {
            currentPlayerSeatIndex = i;
            break;
        }
    }

    // 检查当前玩家的座位是否发生变化
    if (window.previousPlayerSeatIndex !== currentPlayerSeatIndex) {
        needsRecalculatePositions = true;
        window.previousPlayerSeatIndex = currentPlayerSeatIndex;
    }

    // 只有在需要时才重新计算座位显示位置
    if (needsRecalculatePositions) {
        const targetVisualPosition = 3; // 屏幕中下方的视觉位置索引

        // 显示位置映射逻辑：创建映射关系，让当前玩家的座位显示在目标视觉位置
        for (let i = 0; i < 6; i++) {
            if (currentPlayerSeatIndex !== -1) {
                // 计算每个座位号应该显示的视觉位置
                window.seatNum2VisualPosMap[i] = (i - currentPlayerSeatIndex + targetVisualPosition) % 6;
                // 确保结果是正数
                if (window.seatNum2VisualPosMap[i] < 0) {
                    window.seatNum2VisualPosMap[i] += 6;
                }
            } else {
                // 如果当前玩家不在任何座位上，则不调整显示位置
                window.seatNum2VisualPosMap[i] = i;
            }
        }

        console.log('displayPositionMap:', window.seatNum2VisualPosMap);
    }
    // 更新房间信息
    document.getElementById('room-owner').textContent = data.owner ? data.players[data.owner].username : '无';
    document.getElementById('player-count').textContent = Object.keys(data.players).length;

    // 更新当前玩家信息
    if (data.players[user_id]) {
        document.getElementById('player-name').textContent = `玩家昵称：${data.players[user_id].username}`;
        document.getElementById('player-coins').textContent = `金币: ${data.players[user_id].coins}`;

        // 根据玩家状态和游戏状态显示不同的文本
        let statusText = '';

        // 检查玩家是否在座位上
        let isSitting = false;
        for (let i = 0; i < 6; i++) {
            if (data.seats[i] === user_id) {
                isSitting = true;
                break;
            }
        }

        if (data.ready_players && data.ready_players.includes(user_id)) {
            statusText = '已准备';
        } else if (is_playing) {
            statusText = '游戏中';
        } else if (isSitting) {
            statusText = '就座中';
        } else {
            // 玩家不在座位上，显示'溜达中'
            statusText = '溜达中';
        }
        document.getElementById('player-status').textContent = `状态: ${statusText}`;
    }

    // 添加设置头像按钮
    if (!document.getElementById('change-avatar-btn')) {
        const controlsContent = document.querySelector('#control-panel .collapsible-content');
        const btn = document.createElement('button');
        // 房间页面不添加用户信息设置按钮
        // 移除设置玩家信息的按钮
    }

    // 更新座位信息
    // 确保中下方的座位（视觉位置3）始终保持不变
    // 当前玩家的座位应该始终显示在视觉位置3

    // 先清除所有座位的current-player-seat类
    document.querySelectorAll('.seat').forEach(seat => {
        seat.classList.remove('current-player-seat');
    });

    // 创建反向映射：从视觉位置找到对应的座位号
    // 设置为全局变量，供座位点击事件使用
    window.visualPos2SeatNumMap = new Array(6);
    for (let seatNum = 0; seatNum < 6; seatNum++) {
        const visualPos = window.seatNum2VisualPosMap[seatNum];
        if (!isNaN(visualPos) && visualPos !== undefined) {
            window.visualPos2SeatNumMap[visualPos] = seatNum;
        }
    }

    // 在游戏进行中，收集所有有玩家的座位
    let occupiedSeats = [];
    if (is_playing) {
        for (let seatNum = 0; seatNum < 6; seatNum++) {
            if (data.seats[seatNum]) {
                occupiedSeats.push({
                    seatNum: seatNum,
                    playerId: data.seats[seatNum],
                    visualPos: window.seatNum2VisualPosMap[seatNum]
                });
            }
        }

        // 根据玩家相对顺序重新排列座位
        // 1. 找到当前玩家的位置
        let currentPlayerIndex = -1;
        for (let i = 0; i < occupiedSeats.length; i++) {
            if (occupiedSeats[i].playerId === user_id) {
                currentPlayerIndex = i;
                break;
            }
        }

        // 2. 根据玩家数量确定应该使用的座位位置
        const playerCount = occupiedSeats.length;
        const availablePositions = [];
        
        // 根据玩家数量选择最佳的座位布局，确保与CSS布局定义一致
        switch(playerCount) {
            case 2:
                availablePositions.push(3, 0); // 底部中心、顶部中心
                break;
            case 3:
                availablePositions.push(3, 0, 4, 2); // 底部中心、顶部中心、左下角、右下角（确保顺时针排列）
                break;
            case 4:
                availablePositions.push(3, 0, 4, 5, 1, 2); // 底部中心、顶部中心、左下角、左上角、右上角、右下角（确保顺时针排列）
                break;
            case 5:
                availablePositions.push(3, 0, 4, 5, 1, 2); // 底部中心、顶部中心、左下角、左上角、右上角、右下角（确保顺时针排列）
                break;
            case 6:
                availablePositions.push(0, 1, 2, 3, 4, 5); // 所有位置
                break;
            default:
                availablePositions.push(3, 0, 4, 5, 1, 2); // 默认布局（顺时针排列）
        }

        // 3. 重新排列座位，让当前玩家始终在视觉位置3
        if (currentPlayerIndex !== -1 && playerCount > 0) {
            // 创建新的映射关系
            const newVisualPosMap = {};
            
            // 先放置当前玩家到视觉位置3
            const currentPlayer = occupiedSeats[currentPlayerIndex];
            newVisualPosMap[currentPlayer.seatNum] = 3;
            
            // 然后按照顺时针顺序放置其他玩家
            let posIndex = 1; // 从3之后的位置开始
            for (let i = 1; i < playerCount; i++) {
                // 计算要放置的座位索引（顺时针方向）
                const seatToPlaceIndex = (currentPlayerIndex + i) % playerCount;
                const seatToPlace = occupiedSeats[seatToPlaceIndex];
                
                // 找到下一个可用的位置
                while (posIndex < availablePositions.length) {
                    const nextPos = availablePositions[posIndex];
                    // 确保这个位置没有被占用
                    let isOccupied = false;
                    for (const seatNum in newVisualPosMap) {
                        if (newVisualPosMap[seatNum] === nextPos) {
                            isOccupied = true;
                            break;
                        }
                    }
                    
                    if (!isOccupied) {
                        newVisualPosMap[seatToPlace.seatNum] = nextPos;
                        posIndex++;
                        break;
                    }
                    posIndex++;
                }
            }
            
            // 保存新的映射关系
            for (const seatNum in newVisualPosMap) {
                window.seatNum2VisualPosMap[parseInt(seatNum)] = newVisualPosMap[parseInt(seatNum)];
            }
        }
    }

    for (let seatNum = 0; seatNum < 6; seatNum++) {
        // 确定这个座位号应该显示的视觉位置
        const visualPos = window.seatNum2VisualPosMap[seatNum];

        // 如果映射值无效，使用默认值
        if (isNaN(visualPos) || visualPos === undefined) {
            console.error(`无效的映射值：seatNum ${seatNum} -> visualPos ${visualPos}`);
            continue;
        }

        const seat = document.querySelector(`.seat-${visualPos}`);
        const seatNumber = seat.querySelector('.seat-number');
        const playerInfo = seat.querySelector('.player-info');

        // 在游戏进行中，不显示座位号
        if (seatNumber) {
            if (is_playing) {
                seatNumber.style.display = 'none';
            } else {
                seatNumber.textContent = `座位${seatNum + 1}`;
                seatNumber.style.display = 'block';
            }
        }

        // 获取这个座位号上的玩家
        const playerId = data.seats[seatNum];

        if (playerId) {
            // 在游戏进行中，显示有人坐的座位
            if (is_playing) {
                seat.style.display = 'block';
                // 添加status-playing类以确保座位在游戏中显示
                seat.classList.add('status-playing');
            } else {
                // 非游戏状态，移除status-playing类
                seat.classList.remove('status-playing');
            }
            const player = data.players[playerId];
            let statusClass = 'status-normal';
            if (data.ready_players && data.ready_players.includes(playerId)) {
                statusClass = 'status-ready';
                if (playerId === user_id) {
                    is_ready = true;
                    document.getElementById('ready-btn').textContent = '取消准备';
                }
            } else {
                if (playerId === user_id) {
                    is_ready = false;
                    document.getElementById('ready-btn').textContent = '准备就绪';
                }
            }

            // 头像URL处理，添加时间戳防止浏览器缓存头像
            // 简化处理逻辑，直接使用安全的方式添加时间戳
            const timestamp = new Date().getTime();
            // 检查URL是否已经包含查询参数
            // 优先使用avatar_url，同时兼容旧的avatar属性
            let avatarUrlWithTimestamp = player.avatar_url || player.avatar;
            if (avatarUrlWithTimestamp.includes('?')) {
                avatarUrlWithTimestamp = `${avatarUrlWithTimestamp}&t=${timestamp}`;
            } else {
                avatarUrlWithTimestamp = `${avatarUrlWithTimestamp}?t=${timestamp}`;
            }

            // 获取玩家当局已投入金币数，如果没有则默认为0
            // 优先从room_info的player_bets中获取，其次从player对象中获取
            const currentBet = data.player_bets && data.player_bets[playerId] ? data.player_bets[playerId] : (player.current_bet || 0);

            playerInfo.innerHTML = `
                <img class="player-avatar" src="${avatarUrlWithTimestamp}" alt="${player.username}">
                <div class="player-name">${player.username}</div>
                <div class="player-coins">金币: ${player.coins}</div>
                <div class="player-current-bet">已投入: ${currentBet} 金币</div>
                <div class="player-status ${statusClass}">${data.ready_players && data.ready_players.includes(data.seats[seatNum]) ? '已准备' : '未准备'}</div>
            `;

            // 如果是当前用户的座位，添加高亮并定位游戏控制面板
            if (playerId === user_id) {
                seat.classList.add('current-player-seat');
                document.getElementById('stand-up-btn').disabled = false;
                document.getElementById('ready-btn').disabled = false;

                // 动态定位游戏控制面板到当前玩家座位右侧
                positionGameControls(seat);
            }

            // 注意：我们已经在函数开始时统一清除了所有座位的current-player-seat类
            // 所以这里不需要再移除非当前玩家座位的高亮
        } else {
            // 在游戏进行中，不显示空座位
            if (is_playing) {
                seat.style.display = 'none';
            } else {
                seat.style.display = 'block';
                playerInfo.innerHTML = '';
            }
            // 注意：我们已经在函数开始时统一清除了所有座位的current-player-seat类
        }
    }

    // 更新房主控制
    is_owner = user_id === data.owner;
    if (is_owner) {
        document.getElementById('owner-controls').style.display = 'block';
        // 房主时显示编辑房间设置按钮
        document.getElementById('edit-room-settings-btn').style.display = 'block';
        // 房主时隐藏查看房间设置按钮
        document.getElementById('view-room-settings-btn').style.display = 'none';
        // 房主时隐藏规则设置按钮
        document.getElementById('show-settings-modal-btn').style.display = 'none';

        // 更新设置表单
        document.getElementById('setting-235-greater').checked = data.settings.is_235_greater_than_three_of_a_kind;
        document.getElementById('setting-initial-coins').value = data.settings.initial_coins || 1000;
        document.getElementById('setting-base-bet').value = data.settings.base_bet || 1;
        document.getElementById('setting-max-bet').value = data.settings.max_bet !== null ? data.settings.max_bet : 100;
        document.getElementById('setting-max-hands').value = data.settings.max_hands !== null ? data.settings.max_hands : 10;
        document.getElementById('setting-max-pot-amount').value = data.settings.max_pot_amount !== null ? data.settings.max_pot_amount : 1000;

        // 更新踢出玩家下拉框
        const select = document.getElementById('kick-player-select');
        select.innerHTML = '<option value="">无</option>';

        // 添加所有其他玩家
        for (const [player_id, player] of Object.entries(data.players)) {
            if (player_id !== user_id) {
                const option = document.createElement('option');
                option.value = player_id;
                option.textContent = player.username;
                select.appendChild(option);
            }
        }

        // 检查是否可以开始游戏
        const seated_players = data.seats.filter(p => p !== null);
        const all_ready = seated_players.every(p => data.ready_players && data.ready_players.includes(p));
        document.getElementById('start-game-btn').disabled = !(all_ready && seated_players.length >= 2);

        // 如果是新房主并且之前没有打开过设置面板，自动弹出设置面板
        if (data.is_new_owner) {
            setTimeout(() => {
                // 确保从服务器拉取最新的房间设置信息
                if (data.settings) {
                    // 更新设置表单
                    document.getElementById('setting-235-greater').checked = data.settings.is_235_greater_than_three_of_a_kind;
                    document.getElementById('setting-initial-coins').value = data.settings.initial_coins || 1000;
                    document.getElementById('setting-base-bet').value = data.settings.base_bet || 1;
                    document.getElementById('setting-max-bet').value = data.settings.max_bet !== null ? data.settings.max_bet : 100;
                    document.getElementById('setting-max-hands').value = data.settings.max_hands !== null ? data.settings.max_hands : 10;
                }
                // 显示模态框
                const rulesSettingsModal = document.getElementById('rules-settings-modal');
                rulesSettingsModal.style.display = 'block';
            }, 1000);
        }
    } else {
        document.getElementById('owner-controls').style.display = 'none';
        // 非房主时显示查看房间设置按钮
        document.getElementById('view-room-settings-btn').style.display = 'block';
        // 非房主时隐藏编辑房间设置按钮
        document.getElementById('edit-room-settings-btn').style.display = 'none';
        // 非房主时隐藏规则设置按钮
        document.getElementById('show-settings-modal-btn').style.display = 'none';
    }
}

// 开始游戏
function startGame(data) {
    console.log('游戏开始', data);
    is_playing = true;
    document.getElementById('game-status').textContent = '游戏进行中...';
    document.getElementById('game-controls').style.display = 'block';

    // 检测玩家数量，应用相应的座位布局
    const tableInner = document.querySelector('.table-inner');
    // 修复：使用seated_players而不是players来获取玩家数量
    const playerCount = data.seated_players ? data.seated_players.length : 0;

    // 清除之前可能设置的类
    tableInner.classList.remove('two-players-mode', 'three-players-mode', 'four-players-mode', 'five-players-mode');

    // 根据玩家数量应用不同的布局模式
    switch(playerCount) {
        case 2:
            tableInner.classList.add('two-players-mode');
            break;
        case 3:
            tableInner.classList.add('three-players-mode');
            break;
        case 4:
            tableInner.classList.add('four-players-mode');
            break;
        case 5:
            tableInner.classList.add('five-players-mode');
            break;
    }

    // 确保所有有玩家的座位都被标记为status-playing
    if (data.seated_players) {
        data.seated_players.forEach(playerId => {
            // 找到玩家对应的座位
            for (let seatNum = 0; seatNum < 6; seatNum++) {
                if (room_info && room_info.seats[seatNum] === playerId) {
                    const visualPos = window.seatNum2VisualPosMap[seatNum];
                    const seat = document.querySelector(`.seat-${visualPos}`);
                    if (seat) {
                        seat.classList.add('status-playing');
                    }
                    break;
                }
            }
        });
    }
    
    // 确保没有玩家的座位不显示status-playing类
    for (let seatNum = 0; seatNum < 6; seatNum++) {
        if (room_info && !room_info.seats[seatNum]) {
            const visualPos = window.seatNum2VisualPosMap[seatNum];
            const seat = document.querySelector(`.seat-${visualPos}`);
            if (seat) {
                seat.classList.remove('status-playing');
            }
        }
    }

    // 强制重新计算座位显示位置
    // 由于玩家数量可能已经变化，我们需要强制重新计算座位位置
    setTimeout(() => {
        if (room_info) {
            updateRoomInfo(room_info);
        }
    }, 100);

    // 显示所有玩家的手牌（牌背）
    if (data.seated_players) {
        data.seated_players.forEach(playerId => {
            // 找到玩家对应的座位
            for (let seatNum = 0; seatNum < 6; seatNum++) {
                if (room_info && room_info.seats[seatNum] === playerId) {
                    // 获取视觉位置
                    const visualPos = window.seatNum2VisualPosMap[seatNum];
                    const seat = document.querySelector(`.seat-${visualPos}`);
                    
                    if (seat) {
                        const playerInfo = seat.querySelector('.player-info');
                        if (playerInfo) {
                            // 移除之前的手牌显示
                            const oldHand = playerInfo.querySelector('.player-hand');
                            if (oldHand) {
                                oldHand.remove();
                            }
                            
                            // 显示三张牌背
                            let handHtml = '<div class="player-hand">';
                            for (let i = 0; i < 3; i++) {
                                handHtml += `<div class="game-card card-back">🎴</div>`;
                            }
                            handHtml += '</div>';
                            
                            // 添加手牌显示
                            playerInfo.insertAdjacentHTML('beforeend', handHtml);
                        }
                    }
                    break;
                }
            }
        });
    }

    // 显示庄家标识
    if (data.banker && window.visualPos2SeatNumMap && window.seatNum2VisualPosMap) {
        // 遍历所有座位，找到庄家对应的座位
        for (let seatNum = 0; seatNum < 6; seatNum++) {
            const playerId = room_info ? room_info.seats[seatNum] : null;
            if (playerId === data.banker) {
                // 获取庄家座位的视觉位置
                const visualPos = window.seatNum2VisualPosMap[seatNum];
                const bankerSeat = document.querySelector(`.seat-${visualPos}`);
                if (bankerSeat) {
                    const playerInfo = bankerSeat.querySelector('.player-info');
                    // 检查是否已经添加了庄家标识
                    if (!playerInfo.querySelector('.banker-indicator')) {
                        // 添加庄家标识
                        playerInfo.insertAdjacentHTML('afterbegin',
                            '<div class="banker-indicator">🎯 庄家</div>'
                        );
                    }
                }
                break;
            }
        }
    }

    // 更新底池和当前下注信息
    if (!document.getElementById('pot-info')) {
        // 创建显示底池信息的元素
        const gameInfo = document.createElement('div');
        gameInfo.id = 'game-info';
        gameInfo.innerHTML = `
            <div id="pot-info" class="game-info-item">当前底池: ${data.pot || 0} 金币</div>
            <div id="current-bet-info" class="game-info-item">当前下注: ${data.current_bet || 0} 金币</div>
        `;

        // 将游戏信息添加到游戏控制面板上方
        const gameControls = document.getElementById('game-controls');
        if (gameControls && gameControls.parentNode) {
            gameControls.parentNode.insertBefore(gameInfo, gameControls);
        }
    } else {
        // 更新已有的底池和当前下注信息
        document.getElementById('pot-info').textContent = `当前底池: ${data.pot || 0} 金币`;
        document.getElementById('current-bet-info').textContent = `当前下注: ${data.current_bet || 0} 金币`;
    }
}

// 生成预设头像
function generatePresetAvatars() {
    // 优先使用common.js中的函数
    if (typeof loadPresetAvatars === 'function') {
        loadPresetAvatars('.avatar-grid', function(avatarUrl) {
            selectedAvatarUrl = avatarUrl;
            avatarSelected = true;
            const avatarPreview = document.getElementById('avatar-preview');
            if (avatarPreview) {
                avatarPreview.src = avatarUrl;
            }
        });
        return;
    }
    
    // 降级方案 - 如果common.js中的函数不可用
    const grid = document.querySelector('.avatar-grid');
    grid.innerHTML = '';

    // 预设头像列表
    const presetAvatars = [
        '/static/avatars/tuolaji.png',
        '/static/avatars/default.svg',
        '/static/avatars/preset1.svg',
        '/static/avatars/preset2.svg',
        '/static/avatars/preset3.svg',
        '/static/avatars/preset4.svg'
    ];

    // 使用common.js中的函数获取保存的头像设置
    const savedAvatar = (typeof getCurrentUser === 'function' && getCurrentUser()) ? getCurrentUser().avatar_url : null;

    presetAvatars.forEach((avatarUrl, index) => {
        const div = document.createElement('div');
        div.className = 'avatar-option';

        const img = document.createElement('img');
        // 添加时间戳防止浏览器缓存
        const timestamp = new Date().getTime();
        const avatarUrlWithTimestamp = avatarUrl.includes('?')
            ? `${avatarUrl}&t=${timestamp}`
            : `${avatarUrl}?t=${timestamp}`;
        img.src = avatarUrlWithTimestamp;
        img.alt = '预设头像';
        // 使用CSS中定义的样式，不再设置内联样式
        img.style.borderRadius = '0px';
        img.style.cursor = 'pointer';

        div.appendChild(img);
        grid.appendChild(div);

        // 添加点击事件
        div.addEventListener('click', function () {
            // 移除其他头像的选中状态
            document.querySelectorAll('.avatar-option').forEach(option => {
                option.classList.remove('selected');
                option.querySelector('img').style.border = 'none';
            });

            // 添加当前头像的选中状态
            this.classList.add('selected');
            img.style.border = '2px solid blue';

            // 更新预览
            document.getElementById('avatar-preview').src = avatarUrlWithTimestamp;

            // 设置头像
            selectedAvatarUrl = avatarUrlWithTimestamp;
            avatarSelected = true;

            // 只更新本地预览和状态，不单独更新头像，等待用户在信息面板中统一确认
            // setAvatar将在用户确认信息时一起调用
        });

        // 默认选中第一个头像或保存的头像
        if ((index === 0 && !savedAvatar) || (savedAvatar && avatarUrl === savedAvatar.replace(/\?t=\d+$/, ''))) {
            div.classList.add('selected');
            img.style.border = '2px solid blue';

            // 设置头像
            selectedAvatarUrl = savedAvatar || avatarUrlWithTimestamp;
            avatarSelected = true;

            // 更新预览
            document.getElementById('avatar-preview').src = selectedAvatarUrl;
            
            // 只更新本地预览和状态，不单独更新头像，等待用户在信息面板中统一确认
        }
    });
}

// 初始化头像选择
generatePresetAvatars();

// 确保socket连接和user_id处理逻辑正确设置
if (typeof socket !== 'undefined' && socket) {
    // 确保已添加user_id_assigned事件监听
    // 先移除可能已存在的监听器，避免重复
    socket.off('user_id_assigned');
    socket.on(ServerMessageType.UserIDAssigned, function(data) {
        user_id = data.user_id;
        console.log('收到服务器分配的user_id:', user_id);
        // 使用common.js中的函数保存用户ID
        saveUserId(user_id);
        
        // 在收到user_id后再进行后续操作
        // 发送用户名
        if (username) {
            socket.emit(ClientMessageType.SetUserInfo, { [ClientDataKey.Username]: username });
        }
        
        // 如果有房间ID，尝试重新获取房间信息
        if (currentRoomId) {
            console.log('重新获取房间信息');
            socket.emit(ClientMessageType.GetRoomDetails, { [ClientDataKey.RoomID]: currentRoomId });
        }
    });
    
    // 确保connect事件包含重连逻辑
    socket.off('connect');
    socket.on('connect', function() {
        console.log('连接成功');
        // 连接成功后等待服务器发送connected消息
    });
    
    // 接收服务器的连接成功确认消息
    socket.off(ServerMessageType.Connected);
    socket.on(ServerMessageType.Connected, function(data) {
        console.log('收到服务器连接确认:', data);
        
        // 使用common.js中的函数获取用户ID
        const savedUserId = getUserId();
        
        // 如果有保存的user_id，发送给服务器用于重连识别
        if (savedUserId) {
            console.log('使用保存的user_id进行重连:', savedUserId);
            socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: savedUserId });
        } else {
            // 如果没有保存的user_id，也发送reconnect_with_id请求
            // 服务器会分配新的user_id
            console.log('没有保存的user_id，请求分配新ID');
            socket.emit(ClientMessageType.ReconnectWithID, { [ClientDataKey.UserID]: null });
        }
    });
}

// 设置头像 - 只在用户信息面板统一提交时使用
function setAvatar(avatarUrl) {
    // 只更新本地状态，不发送Socket消息
    // 等待用户在信息面板中统一提交用户名和头像
    selectedAvatarUrl = avatarUrl;
    avatarSelected = true;
    
    // 更新预览
    const avatarPreview = document.getElementById('avatar-preview');
    if (avatarPreview) {
        avatarPreview.src = avatarUrl;
    }
}

// 上传头像
document.getElementById('upload-avatar-btn').addEventListener('click', function () {
    // 优先使用common.js中的函数上传头像
    if (typeof uploadAvatar === 'function') {
        uploadAvatar(socket, user_id, username);
    } else {
        // 如果common.js中的函数不可用，使用原有的上传逻辑
        console.log('点击上传头像按钮');
        const fileInput = document.getElementById('avatar-upload');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            console.log('选择的文件:', file);
            const formData = new FormData();
            formData.append('file', file);

            console.log('Socket状态:', socket ? '已连接' : '未连接');
            console.log('User ID:', user_id);

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
                    if (data.avatar_url) {
                        // 添加时间戳防止浏览器缓存
                        const timestamp = new Date().getTime();
                        const avatarUrlWithTimestamp = data.avatar_url.includes('?')
                            ? `${data.avatar_url}&t=${timestamp}`
                            : `${data.avatar_url}?t=${timestamp}`;

                        // 更新预览
                        document.getElementById('avatar-preview').src = avatarUrlWithTimestamp;

                        // 设置头像
                        selectedAvatarUrl = avatarUrlWithTimestamp;
                        avatarSelected = true;

                        // 清除其他选中状态
                        document.querySelectorAll('.avatar-option').forEach(option => {
                            option.classList.remove('selected');
                            if (option.querySelector('img')) {
                                option.querySelector('img').style.border = 'none';
                            }
                        });

                        // 更新本地状态，不单独更新头像
                        selectedAvatarUrl = avatarUrlWithTimestamp;
                        avatarSelected = true;
                        
                        // 只在用户确认信息面板时才会真正更新
                        alert('头像上传成功，请在用户信息面板中点击确认按钮保存修改');
                    } else {
                        alert('头像上传失败: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('上传头像时发生错误:', error);
                    alert('头像上传失败: ' + error.message);
                });
        } else {
            alert('请选择一个文件');
        }
    }
});

// 初始化页面
function initializePage() {
    // 添加私有房间复选框事件监听器
    const isPrivateCheckbox = document.getElementById('is-private');
    if (isPrivateCheckbox) {
        isPrivateCheckbox.addEventListener('change', togglePrivatePassword);
    }
    
    // 初始时隐藏密码输入框
    togglePrivatePassword();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置SocketIO事件监听器
    setupSocketListeners();
    // 初始化页面
    initializePage();
    
    // 添加查看规则按钮点击事件
    const viewRulesBtn = document.getElementById('view-rules-btn');
    if (viewRulesBtn) {
        viewRulesBtn.addEventListener('click', function () {
            // 使用common.js中的函数显示模态框
            if (typeof showModal === 'function') {
                showModal('rules-modal');
            } else {
                document.getElementById('rules-modal').classList.add('show');
            }
        });
    }
    
    // 添加关闭规则模态框按钮点击事件
    const closeRulesModalBtn = document.getElementById('close-rules-modal-btn');
    if (closeRulesModalBtn) {
        closeRulesModalBtn.addEventListener('click', function () {
            // 使用common.js中的函数隐藏模态框
            if (typeof hideModal === 'function') {
                hideModal('rules-modal');
            } else {
                document.getElementById('rules-modal').classList.remove('show');
            }
        });
    }
    
    // 添加继续游戏按钮点击事件
    const continueYesBtn = document.getElementById('continue-yes-btn');
    if (continueYesBtn) {
        continueYesBtn.addEventListener('click', function () {
            socket.emit(ClientMessageType.ContinueGame, { [ClientDataKey.ContinueGame]: true });
            // 使用common.js中的函数隐藏模态框
            if (typeof hideModal === 'function') {
                hideModal('continue-modal');
            } else {
                document.getElementById('continue-modal').classList.remove('show');
            }
        });
    }
    
    // 添加退出游戏按钮点击事件
    const continueNoBtn = document.getElementById('continue-no-btn');
    if (continueNoBtn) {
        continueNoBtn.addEventListener('click', function () {
            socket.emit(ClientMessageType.ContinueGame, { [ClientDataKey.ContinueGame]: false });
            // 使用common.js中的函数隐藏模态框
            if (typeof hideModal === 'function') {
                hideModal('continue-modal');
            } else {
                document.getElementById('continue-modal').classList.remove('show');
            }
        });
    }
    
    // 获取所有可折叠面板头部
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');

    // 为每个头部添加点击事件
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function () {
            // 获取父面板
            const panel = this.parentElement;
            // 获取内容区域
            const content = this.nextElementSibling;
            // 获取图标
            const icon = this.querySelector('.collapsible-icon');

            // 切换内容显示状态
            if (panel.classList.contains('collapsed')) {
                // 展开内容
                panel.classList.remove('collapsed');
                // 更新图标
                icon.textContent = '▲';
            } else {
                // 折叠内容
                panel.classList.add('collapsed');
                // 更新图标，确保折叠时显示向下的三角形
                icon.textContent = '▼';
            }
        });

        // 初始化时默认展开所有面板 - 不设置最大高度，允许内容自适应
    });
    
    // 点击模态框外部关闭模态框
    window.addEventListener('click', function (event) {
        const userSetupModal = document.getElementById('user-setup-modal');
        const rulesModal = document.getElementById('rules-modal');
        const continueModal = document.getElementById('continue-modal');
        const rulesSettingsModal = document.getElementById('rules-settings-modal');
        const viewRoomSettingsModal = document.getElementById('view-room-settings-modal');
        const roomListModal = document.getElementById('room-list-modal');
        const createRoomModal = document.getElementById('create-room-modal');

        if (event.target === userSetupModal) {
            // 不允许点击外部关闭用户设置模态框，用户必须完成设置
        } else if (typeof hideModal === 'function') {
            // 使用common.js中的函数关闭模态框
            if (event.target === rulesModal) {
                hideModal('rules-modal');
            } else if (event.target === continueModal) {
                hideModal('continue-modal');
            } else if (event.target === rulesSettingsModal) {
        // 使用common.js中的函数隐藏模态框
        if (typeof hideModal === 'function') {
            hideModal('rules-settings-modal');
        } else {
            rulesSettingsModal.classList.remove('show');
            rulesSettingsModal.style.display = 'none';
        }
    } else if (event.target === viewRoomSettingsModal) {
        // 使用common.js中的函数隐藏模态框
        if (typeof hideModal === 'function') {
            hideModal('view-room-settings-modal');
        } else {
            viewRoomSettingsModal.classList.remove('show');
            viewRoomSettingsModal.style.display = 'none';
        }
            } else if (event.target === roomListModal) {
                hideModal('room-list-modal');
            } else if (event.target === createRoomModal) {
                hideModal('create-room-modal');
            }
        } else {
            // 备用方案 - 如果common.js中的函数不可用
            if (event.target === rulesModal) {
                rulesModal.classList.remove('show');
            } else if (event.target === continueModal) {
                continueModal.classList.remove('show');
            } else if (event.target === rulesSettingsModal) {
                rulesSettingsModal.classList.remove('show');
            } else if (event.target === viewRoomSettingsModal) {
                viewRoomSettingsModal.classList.remove('show');
            } else if (event.target === roomListModal) {
                roomListModal.classList.remove('show');
            } else if (event.target === createRoomModal) {
                createRoomModal.classList.remove('show');
            }
        }
    });
})