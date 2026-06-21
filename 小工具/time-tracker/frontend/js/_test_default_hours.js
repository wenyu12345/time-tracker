// 纯逻辑测试：验证默认工时逻辑（脱离 DOM）
const DEFAULT_HOURS = {
    '白班': 11,
    '夜班': 11.5
};
const EARLY_OFF_HOURS = 8;

function simulateHandleRecordTypeChange(recordType, shiftType, preserveHours, currentHours) {
    // 模拟 handleRecordTypeChange 的核心逻辑，返回新的工时值
    let hours = currentHours;
    if (!preserveHours) {
        hours = '';
    }
    if (recordType === 'leave') {
        return { hours: preserveHours ? hours : '', shiftVisible: false };
    } else if (recordType === 'early-off') {
        if (!preserveHours) hours = String(EARLY_OFF_HOURS);
        return { hours, shiftVisible: true };
    } else {
        if (!preserveHours && shiftType && DEFAULT_HOURS[shiftType] !== undefined) {
            hours = String(DEFAULT_HOURS[shiftType]);
        }
        return { hours, shiftVisible: true };
    }
}

function simulateHandleShiftTypeChange(recordType, shiftType) {
    // 模拟 handleShiftTypeChange 的核心逻辑
    if (recordType === 'leave' || recordType === 'early-off') return null;
    if (shiftType && DEFAULT_HOURS[shiftType] !== undefined) {
        return String(DEFAULT_HOURS[shiftType]);
    }
    return null;
}

let passed = 0;
let failed = 0;

function assert(desc, actual, expected) {
    if (actual === expected) {
        console.log('  ✓ ' + desc);
        passed++;
    } else {
        console.log('  ✗ ' + desc + ' (actual=' + actual + ', expected=' + expected + ')');
        failed++;
    }
}

console.log('=== 场景 1：全新创建 + 白班 ===');
let r = simulateHandleRecordTypeChange('normal', '白班', false, null);
assert('工时=11', r.hours, '11');
assert('班别可见', r.shiftVisible, true);

console.log('=== 场景 2：全新创建 + 夜班 ===');
r = simulateHandleRecordTypeChange('normal', '夜班', false, null);
assert('工时=11.5', r.hours, '11.5');

console.log('=== 场景 3：全新创建 + 下早班 ===');
r = simulateHandleRecordTypeChange('early-off', '白班', false, null);
assert('工时=8', r.hours, '8');

console.log('=== 场景 4：已有记录回填（白班 10 小时，不应该被覆盖为 11） ===');
r = simulateHandleRecordTypeChange('normal', '白班', true, '10.0');
assert('工时保留10.0', r.hours, '10.0');

console.log('=== 场景 5：已有记录回填（夜班 11 小时，不应该被覆盖为 11.5） ===');
r = simulateHandleRecordTypeChange('normal', '夜班', true, '11.0');
assert('工时保留11.0', r.hours, '11.0');

console.log('=== 场景 6：用户切换班别（白班→夜班）===');
let h = simulateHandleShiftTypeChange('normal', '夜班');
assert('工时变为11.5', h, '11.5');

console.log('=== 场景 7：用户切换班别（夜班→白班）===');
h = simulateHandleShiftTypeChange('normal', '白班');
assert('工时变为11', h, '11');

console.log('=== 场景 8：请假状态下切换班别应无操作 ===');
h = simulateHandleShiftTypeChange('leave', '白班');
assert('不操作', h, null);

console.log('=== 场景 9：下早班状态下切换班别应无操作 ===');
h = simulateHandleShiftTypeChange('early-off', '夜班');
assert('不操作', h, null);

console.log();
console.log('结果：' + passed + ' 通过，' + failed + ' 失败');
if (failed > 0) process.exit(1);
