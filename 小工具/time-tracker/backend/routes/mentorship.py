from flask import Blueprint, request, jsonify
from utils.db import get_db
from datetime import datetime
import sqlite3

mentorship_bp = Blueprint('mentorship', __name__)


# ============================================================
# 拼音首字母工具：常见中文姓氏和常用字首字母映射表
# （简洁版：覆盖常用中文姓氏和常见字，足够用于首字母搜索
# ============================================================

# 常用中文拼音首字母映射表（按Unicode范围及常用字映射）
_PINYIN_INITIAL_TABLE = {
    # 常见姓氏和常用字（补充）
    '赵': 'Z', '钱': 'Q', '孙': 'S', '李': 'L', '周': 'Z', '吴': 'W',
    '郑': 'Z', '王': 'W', '冯': 'F', '陈': 'C', '褚': 'C', '卫': 'W',
    '蒋': 'J', '沈': 'S', '韩': 'H', '杨': 'Y', '朱': 'Z', '秦': 'Q',
    '尤': 'Y', '许': 'X', '何': 'H', '吕': 'L', '施': 'S', '张': 'Z',
    '孔': 'K', '曹': 'C', '严': 'Y', '华': 'H', '金': 'J', '魏': 'W',
    '陶': 'T', '姜': 'J', '戚': 'Q', '谢': 'X', '邹': 'Z', '喻': 'Y',
    '柏': 'B', '水': 'S', '窦': 'D', '章': 'Z', '云': 'Y', '苏': 'S',
    '潘': 'P', '葛': 'G', '奚': 'X', '范': 'F', '彭': 'P', '郎': 'L',
    '鲁': 'L', '韦': 'W', '昌': 'C', '马': 'M', '苗': 'M', '凤': 'F',
    '花': 'H', '方': 'F', '俞': 'Y', '任': 'R', '袁': 'Y', '柳': 'L',
    '唐': 'T', '罗': 'L', '费': 'F', '廉': 'L', '岑': 'C', '薛': 'X',
    '雷': 'L', '贺': 'H', '倪': 'N', '汤': 'T', '滕': 'T', '殷': 'Y',
    '罗': 'L', '毕': 'B', '郝': 'H', '邬': 'W', '安': 'A', '常': 'C',
    '乐': 'L', '时': 'S', '傅': 'F', '皮': 'P', '卞': 'B', '齐': 'Q',
    '康': 'K', '伍': 'W', '余': 'Y', '元': 'Y', '卜': 'B', '顾': 'G',
    '孟': 'M', '平': 'P', '黄': 'H', '和': 'H', '穆': 'M', '萧': 'X',
    '尹': 'Y', '姚': 'Y', '邵': 'S', '堪': 'K', '汪': 'W', '祁': 'Q',
    '毛': 'M', '禹': 'Y', '狄': 'D', '米': 'M', '贝': 'B', '明': 'M',
    '臧': 'Z', '计': 'J', '成': 'C', '戴': 'D', '谈': 'T', '宋': 'S',
    '茅': 'M', '庞': 'P', '熊': 'X', '纪': 'J', '舒': 'S', '屈': 'Q',
    '项': 'X', '祝': 'Z', '董': 'D', '梁': 'L', '阮': 'R', '江': 'J',
    '童': 'T', '颜': 'Y', '郭': 'G', '梅': 'M', '盛': 'S', '林': 'L',
    '刁': 'D', '钟': 'Z', '徐': 'X', '邱': 'Q', '骆': 'L', '高': 'G',
    '樊': 'F', '夏': 'X', '蔡': 'C', '田': 'T', '樊': 'F', '胡': 'H',
    '凌': 'L', '霍': 'H', '虞': 'Y', '万': 'W', '支': 'Z', '柯': 'K',
    '昝': 'Z', '卢': 'L', '莫': 'M', '经': 'J', '房': 'F', '裘': 'Q',
    '缪': 'M', '干': 'G', '解': 'X', '应': 'Y', '宗': 'Z', '丁': 'D',
    '宣': 'X', '贲': 'B', '邓': 'D', '郁': 'Y', '单': 'S', '杭': 'H',
    '洪': 'H', '包': 'B', '诸': 'Z', '左': 'Z', '石': 'S', '崔': 'C',
    '吉': 'J', '钮': 'N', '龚': 'G', '程': 'C', '嵇': 'J', '滑': 'H',
    '裴': 'P', '陆': 'L', '荣': 'R', '翁': 'W', '荀': 'X', '羊': 'Y',
    '于': 'Y', '甄': 'Z', '曲': 'Q', '家': 'J', '封': 'F', '芮': 'R',
    '羿': 'Y', '储': 'C', '靳': 'J', '糜': 'M', '松': 'S', '井': 'J',
    '段': 'D', '富': 'F', '巫': 'W', '乌': 'W', '焦': 'J', '巴': 'B',
    '弓': 'G', '牧': 'M', '隗': 'K', '山': 'S', '谷': 'G', '车': 'C',
    '侯': 'H', '宓': 'M', '蓬': 'P', '全': 'Q', '郗': 'X', '班': 'B',
    '仰': 'Y', '秋': 'Q', '仲': 'Z', '伊': 'Y', '宫': 'G', '宁': 'N',
    '仇': 'Q', '栾': 'L', '甘': 'G', '钭': 'D', '厉': 'L', '戎': 'R',
    '祖': 'Z', '幸': 'X', '逢': 'F', '景': 'J', '韶': 'S', '郜': 'G',
    '黎': 'L', '蓟': 'J', '薄': 'B', '印': 'Y', '宿': 'S', '白': 'B',
    '怀': 'H', '蒲': 'P', '邰': 'T', '从': 'C', '鄂': 'E', '索': 'S',
    '咸': 'X', '籍': 'J', '赖': 'L', '卓': 'Z', '蔺': 'L', '屠': 'T',
    '蒙': 'M', '池': 'C', '乔': 'Q', '阴': 'Y', '胥': 'X', '闻': 'W',
    '莘': 'X', '党': 'D', '翟': 'Z', '谭': 'T', '贡': 'G', '劳': 'L',
    '冉': 'R', '宰': 'Z', '郦': 'L', '雍': 'Y', '却': 'Q', '璩': 'Q',
    '桑': 'S', '桂': 'G', '濮': 'P', '牛': 'N', '寿': 'S', '通': 'T',
    '边': 'B', '扈': 'H', '燕': 'Y', '冀': 'J', '郏': 'J', '浦': 'P',
    '尚': 'S', '农': 'N', '温': 'W', '别': 'B', '庄': 'Z', '晏': 'Y',
    '柴': 'C', '充': 'C', '慕': 'M', '连': 'L', '慕': 'M', '习': 'X',
    '向': 'X', '古': 'G', '易': 'Y', '慎': 'S', '戈': 'G', '廖': 'L',
    '暨': 'J', '居': 'J', '衡': 'H', '步': 'B', '都': 'D', '耿': 'G',
    '满': 'M', '弘': 'H', '匡': 'K', '国': 'G', '文': 'W', '寇': 'K',
    '广': 'G', '禄': 'L', '阙': 'Q', '东': 'D', '欧': 'O', '殳': 'S',
    '沃': 'W', '利': 'L', '蔚': 'W', '越': 'Y', '夔': 'K', '隆': 'L',
    '师': 'S', '巩': 'G', '厍': 'S', '聂': 'N', '晁': 'C', '勾': 'G',
    '融': 'R', '冷': 'L', '訾': 'Z', '辛': 'X', '阚': 'K', '那': 'N',
    '饶': 'R', '空': 'K', '曾': 'Z', '毋': 'W', '沙': 'S', '乜': 'N',
    '养': 'Y', '鞠': 'J', '须': 'X', '丰': 'F', '巢': 'C', '关': 'G',
    '蒯': 'K', '相': 'X', '查': 'Z', '后': 'H', '荆': 'J', '游': 'Y',
    '竺': 'Z', '权': 'Q', '逯': 'L', '盖': 'G', '益': 'Y', '桓': 'H',
    '公': 'G', '万': 'W', '俟': 'Q', '司': 'S', '上官': 'S',
    # 常见名字用字
    '伟': 'W', '芳': 'F', '娜': 'N', '敏': 'M', '静': 'J', '丽': 'L',
    '强': 'Q', '磊': 'L', '军': 'J', '洋': 'Y', '勇': 'Y', '艳': 'Y',
    '杰': 'J', '娟': 'J', '涛': 'T', '明': 'M', '秀': 'X', '霞': 'X',
    '平': 'P', '刚': 'G', '桂': 'G', '英': 'Y', '华': 'H', '慧': 'H',
    '强': 'Q', '琳': 'L', '欣': 'X', '瑶': 'Y', '怡': 'Y', '超': 'C',
    '兰': 'L', '洁': 'J', '鑫': 'X', '文': 'W', '鹏': 'P', '博': 'B',
    '智': 'Z', '丹': 'D', '彤': 'T', '嘉': 'J', '琪': 'Q', '婷': 'T',
    '涵': 'H', '慧': 'H', '琳': 'L', '璐': 'L', '然': 'R', '欣': 'X',
    '若': 'R', '雪': 'X', '梦': 'M', '洁': 'J', '菲': 'F', '菲': 'F',
    '一': 'Y', '二': 'E', '三': 'S', '四': 'S', '五': 'W', '六': 'L',
    '七': 'Q', '八': 'B', '九': 'J', '十': 'S', '小': 'X', '大': 'D',
    '春': 'C', '夏': 'X', '秋': 'Q', '冬': 'D', '红': 'H', '梅': 'M',
    '兰': 'L', '竹': 'Z', '菊': 'J', '松': 'S', '柏': 'B', '柳': 'L',
    '云': 'Y', '风': 'F', '雨': 'Y', '雪': 'X', '山': 'S', '川': 'C',
    '石': 'S', '玉': 'Y', '珠': 'Z', '金': 'J', '银': 'Y', '宝': 'B',
    '财': 'C', '富': 'F', '贵': 'G', '福': 'F', '寿': 'S', '喜': 'X',
    '吉': 'J', '祥': 'X', '安': 'A', '康': 'K', '健': 'J', '壮': 'Z',
    '美': 'M', '丽': 'L', '好': 'H', '善': 'S', '德': 'D', '才': 'C',
    '贤': 'X', '能': 'N', '勤': 'Q', '俭': 'J', '朴': 'P', '实': 'S',
    '真': 'Z', '诚': 'C', '信': 'X', '义': 'Y', '礼': 'L', '智': 'Z',
    '仁': 'R', '爱': 'A', '友': 'Y', '和': 'H', '平': 'P', '正': 'Z',
    '直': 'Z', '公': 'G', '平': 'P', '光': 'G', '明': 'M', '辉': 'H',
    '辉': 'H', '煌': 'H', '灿': 'C', '烂': 'L', '耀': 'Y', '光': 'G',
    '荣': 'R', '华': 'H', '富': 'F', '强': 'Q', '胜': 'S', '利': 'L',
    '建': 'J', '设': 'S', '国': 'G', '家': 'J', '业': 'Y', '平': 'P',
    '安': 'A', '全': 'Q', '稳': 'W', '定': 'D', '固': 'G', '牢': 'L',
    '发': 'F', '展': 'Z', '扩': 'K', '大': 'D', '小': 'X', '中': 'Z',
    '新': 'X', '旧': 'J', '老': 'L', '少': 'S', '幼': 'Y', '男': 'N',
    '女': 'N', '夫': 'F', '妻': 'Q', '子': 'Z', '女': 'N', '父': 'F',
    '母': 'M', '哥': 'G', '弟': 'D', '姐': 'J', '妹': 'M', '叔': 'S',
    '伯': 'B', '叔': 'S', '舅': 'J', '姑': 'G', '姨': 'Y', '婶': 'S',
    '侄': 'Z', '媳': 'X', '孙': 'S', '婿': 'X', '姥': 'L', '爷': 'Y',
    '奶': 'N', '姥': 'L', '公': 'G', '婆': 'P', '爸': 'B', '妈': 'M',
    '师': 'S', '傅': 'F', '徒': 'T', '弟': 'D', '子': 'Z', '员': 'Y',
    '工': 'G', '人': 'R', '民': 'M', '众': 'Z', '群': 'Q', '团': 'T',
    '队': 'D', '班': 'B', '组': 'Z', '科': 'K', '室': 'S', '部': 'B',
    '科': 'K', '技': 'J', '术': 'S', '艺': 'Y', '术': 'S', '学': 'X',
    '习': 'X', '教': 'J', '育': 'Y', '练': 'L', '练': 'L', '操': 'C',
    '作': 'Z', '业': 'Y', '事': 'S', '情': 'Q', '感': 'G', '觉': 'J',
    '想': 'X', '思': 'S', '念': 'N', '忘': 'W', '记': 'J', '忆': 'Y',
    '志': 'Z', '愿': 'Y', '意': 'Y', '志': 'Z', '心': 'X', '情': 'Q',
    '爱': 'A', '恨': 'H', '喜': 'X', '怒': 'N', '哀': 'A', '乐': 'L',
    '悲': 'B', '欢': 'H', '怒': 'N', '恐': 'K', '惧': 'J', '怕': 'P',
    '惊': 'J', '慌': 'H', '吓': 'X', '怕': 'P', '羞': 'X', '耻': 'C',
    '愧': 'K', '悔': 'H', '恨': 'H', '怒': 'N', '怨': 'Y', '愤': 'F',
    '怒': 'N', '怒': 'N', '怒': 'N',
}


def _get_pinyin_initial(ch):
    """获取单个字符的拼音首字母

    参数:
        ch: 单个字符
    返回:
        大写首字母，或原字符（非中文字符原样返回）
    """
    if ch is None:
        return ''
    if len(ch) == 0:
        return ''
    # ASCII字符直接返回
    if ord(ch) < 128:
        return ch.upper() if ch.isalpha() else ''
    # 优先使用 pypinyin 库
    try:
        from pypinyin import lazy_pinyin, Style
        result = lazy_pinyin(ch, style=Style.FIRST_LETTER)
        if result and result[0] and result[0].isalpha():
            return result[0].upper()
    except Exception:
        pass
    # 从表中查找
    if ch in _PINYIN_INITIAL_TABLE:
        return _PINYIN_INITIAL_TABLE[ch]
    # 使用Unicode区间粗略匹配（按拼音首字母分区估算）
    code = ord(ch)
    # 根据Unicode常用字区间估算（常用中文 Unicode 范围划分（粗略拼音首字母映射
    # （使用常用字分区映射）
    ranges = [
        # (开始, 结束, 首字母)
        (0x4e00, 0x4e0f, 'Y'), (0x4e10, 0x4e1f, 'D'), (0x4e20, 0x4e2f, 'Y'),
        (0x4e30, 0x4e3f, 'L'), (0x4e40, 0x4e4f, 'Q'), (0x4e50, 0x4e5f, 'E'),
        (0x4e60, 0x4e6f, 'G'), (0x4e70, 0x4e7f, 'W'), (0x4e80, 0x4e8f, 'R'),
        (0x4e90, 0x4e9f, 'Z'), (0x4ea0, 0x4eaf, 'S'), (0x4eb0, 0x4ebf, 'J'),
        (0x4ec0, 0x4ecf, 'Q'), (0x4ed0, 0x4edf, 'Y'), (0x4ee0, 0x4eef, 'C'),
        (0x4ef0, 0x4eff, 'H'), (0x4f00, 0x4f0f, 'G'), (0x4f10, 0x4f1f, 'Y'),
        (0x4f20, 0x4f2f, 'H'), (0x4f30, 0x4f3f, 'Z'), (0x4f40, 0x4f4f, 'N'),
        (0x4f50, 0x4f5f, 'B'), (0x4f60, 0x4f6f, 'M'), (0x4f70, 0x4f7f, 'X'),
        (0x4f80, 0x4f8f, 'J'), (0x4f90, 0x4f9f, 'Z'), (0x4fa0, 0x4faf, 'C'),
        (0x4fb0, 0x4fbf, 'Z'), (0x4fc0, 0x4fcf, 'D'), (0x4fd0, 0x4fdf, 'C'),
        (0x4fe0, 0x4fef, 'X'), (0x4ff0, 0x4fff, 'Y'), (0x5000, 0x500f, 'K'),
        (0x5010, 0x501f, 'L'), (0x5020, 0x502f, 'H'), (0x5030, 0x503f, 'L'),
        (0x5040, 0x504f, 'M'), (0x5050, 0x505f, 'N'), (0x5060, 0x506f, 'B'),
        (0x5070, 0x507f, 'Y'), (0x5080, 0x508f, 'Q'), (0x5090, 0x509f, 'B'),
        (0x50a0, 0x50af, 'T'), (0x50b0, 0x50bf, 'Y'), (0x50c0, 0x50cf, 'X'),
        (0x50d0, 0x50df, 'X'), (0x50e0, 0x50ef, 'J'), (0x50f0, 0x50ff, 'S'),
        (0x5100, 0x510f, 'G'), (0x5110, 0x511f, 'C'), (0x5120, 0x512f, 'L'),
        (0x5130, 0x513f, 'P'), (0x5140, 0x514f, 'N'), (0x5150, 0x515f, 'C'),
        (0x5160, 0x516f, 'Y'), (0x5170, 0x517f, 'Q'), (0x5180, 0x518f, 'C'),
        (0x5190, 0x519f, 'S'), (0x51a0, 0x51af, 'J'), (0x51b0, 0x51bf, 'L'),
        (0x51c0, 0x51cf, 'L'), (0x51d0, 0x51df, 'Y'), (0x51e0, 0x51ef, 'Z'),
        (0x51f0, 0x51ff, 'Y'), (0x5200, 0x520f, 'C'), (0x5210, 0x521f, 'L'),
        (0x5220, 0x522f, 'Y'), (0x5230, 0x523f, 'L'), (0x5240, 0x524f, 'D'),
        (0x5250, 0x525f, 'L'), (0x5260, 0x526f, 'B'), (0x5270, 0x527f, 'J'),
        (0x5280, 0x528f, 'Z'), (0x5290, 0x529f, 'X'), (0x52a0, 0x52af, 'F'),
        (0x52b0, 0x52bf, 'H'), (0x52c0, 0x52cf, 'S'), (0x52d0, 0x52df, 'Q'),
        (0x52e0, 0x52ef, 'Q'), (0x52f0, 0x52ff, 'Q'), (0x5300, 0x530f, 'W'),
        (0x5310, 0x531f, 'L'), (0x5320, 0x532f, 'S'), (0x5330, 0x533f, 'H'),
        (0x5340, 0x534f, 'Q'), (0x5350, 0x535f, 'X'), (0x5360, 0x536f, 'Y'),
        (0x5370, 0x537f, 'S'), (0x5380, 0x538f, 'M'), (0x5390, 0x539f, 'H'),
        (0x53a0, 0x53af, 'T'), (0x53b0, 0x53bf, 'T'), (0x53c0, 0x53cf, 'T'),
        (0x53d0, 0x53df, 'Y'), (0x53e0, 0x53ef, 'P'), (0x53f0, 0x53ff, 'T'),
        (0x5400, 0x540f, 'S'), (0x5410, 0x541f, 'Y'), (0x5420, 0x542f, 'H'),
        (0x5430, 0x543f, 'Y'), (0x5440, 0x544f, 'Y'), (0x5450, 0x545f, 'T'),
        (0x5460, 0x546f, 'J'), (0x5470, 0x547f, 'Q'), (0x5480, 0x548f, 'Z'),
        (0x5490, 0x549f, 'X'), (0x54a0, 0x54af, 'J'), (0x54b0, 0x54bf, 'J'),
        (0x54c0, 0x54cf, 'X'), (0x54d0, 0x54df, 'H'), (0x54e0, 0x54ef, 'X'),
        (0x54f0, 0x54ff, 'Y'), (0x5500, 0x550f, 'S'), (0x5510, 0x551f, 'X'),
        (0x5520, 0x552f, 'D'), (0x5530, 0x553f, 'M'), (0x5540, 0x554f, 'T'),
        (0x5550, 0x555f, 'Y'), (0x5560, 0x556f, 'B'), (0x5570, 0x557f, 'L'),
        (0x5580, 0x558f, 'B'), (0x5590, 0x559f, 'Y'), (0x55a0, 0x55af, 'J'),
        (0x55b0, 0x55bf, 'X'), (0x55c0, 0x55cf, 'Q'), (0x55d0, 0x55df, 'Z'),
        (0x55e0, 0x55ef, 'B'), (0x55f0, 0x55ff, 'J'), (0x5600, 0x560f, 'C'),
        (0x5610, 0x561f, 'X'), (0x5620, 0x562f, 'L'), (0x5630, 0x563f, 'Y'),
        (0x5640, 0x564f, 'H'), (0x5650, 0x565f, 'H'), (0x5660, 0x566f, 'J'),
        (0x5670, 0x567f, 'D'), (0x5680, 0x568f, 'L'), (0x5690, 0x569f, 'Q'),
        (0x56a0, 0x56af, 'C'), (0x56b0, 0x56bf, 'X'), (0x56c0, 0x56cf, 'L'),
        (0x56d0, 0x56df, 'H'), (0x56e0, 0x56ef, 'X'), (0x56f0, 0x56ff, 'J'),
        (0x5700, 0x570f, 'B'), (0x5710, 0x571f, 'Y'), (0x5720, 0x572f, 'G'),
        (0x5730, 0x573f, 'Q'), (0x5740, 0x574f, 'Y'), (0x5750, 0x575f, 'L'),
        (0x5760, 0x576f, 'Y'), (0x5770, 0x577f, 'B'), (0x5780, 0x578f, 'G'),
        (0x5790, 0x579f, 'D'), (0x57a0, 0x57af, 'L'), (0x57b0, 0x57bf, 'Z'),
        (0x57c0, 0x57cf, 'Y'), (0x57d0, 0x57df, 'Y'), (0x57e0, 0x57ef, 'B'),
        (0x57f0, 0x57ff, 'J'), (0x5800, 0x580f, 'C'), (0x5810, 0x581f, 'D'),
        (0x5820, 0x582f, 'Z'), (0x5830, 0x583f, 'G'), (0x5840, 0x584f, 'L'),
        (0x5850, 0x585f, 'C'), (0x5860, 0x586f, 'C'), (0x5870, 0x587f, 'Y'),
        (0x5880, 0x588f, 'W'), (0x5890, 0x589f, 'Y'), (0x58a0, 0x58af, 'H'),
        (0x58b0, 0x58bf, 'H'), (0x58c0, 0x58cf, 'H'), (0x58d0, 0x58df, 'Z'),
        (0x58e0, 0x58ef, 'H'), (0x58f0, 0x58ff, 'T'), (0x5900, 0x590f, 'M'),
        (0x5910, 0x591f, 'J'), (0x5920, 0x592f, 'C'), (0x5930, 0x593f, 'X'),
        (0x5940, 0x594f, 'Q'), (0x5950, 0x595f, 'J'), (0x5960, 0x596f, 'J'),
        (0x5970, 0x597f, 'J'), (0x5980, 0x598f, 'D'), (0x5990, 0x599f, 'D'),
    ]
    for start, end, initial in ranges:
        if start <= code <= end:
            return initial
    return '?'


def get_pinyin_initials(text):
    """获取字符串的拼音首字母组合

    参数:
        text: 输入的中文字符串（姓名等）
    返回:
        大写首字母组合，例如 "张坤" -> "ZK"，"张三峰" -> "ZSF"
    """
    if not text:
        return ''
    try:
        from pypinyin import lazy_pinyin, Style
        initials = lazy_pinyin(text, style=Style.FIRST_LETTER)
        result = ''.join([c.upper() for c in initials if c and c.isalpha()])
        return result or text[0].upper()
    except Exception:
        pass
    # 回退：使用手动字典
    result = ''
    for ch in text:
        initial = _get_pinyin_initial(ch)
        if initial and initial != '?':
            result += initial
    return result or (text[0].upper() if text else '')


def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    return d


def get_user_info(user_id):
    """获取用户基本信息"""
    db = get_db()
    row = db.execute(
        "SELECT id, username, shift_type, is_active, hire_date, role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'shift_type': row['shift_type'],
            'is_active': row['is_active'],
            'hire_date': row['hire_date'],
            'role': row['role']
        }
    return None


def build_tree(root_id, visited=None):
    """
    递归构建从某个根节点开始的树状结构
    返回: { user: {...}, apprentices: [ {...}, ... ] }
    """
    if visited is None:
        visited = set()
    if root_id in visited:
        return None  # 防止循环
    visited.add(root_id)

    db = get_db()
    user_info = get_user_info(root_id)
    if not user_info:
        return None

    # 获取该用户作为师傅的所有徒弟
    apprentices_rows = db.execute(
        """SELECT m.id, m.apprentice_id, m.relationship_type, m.start_date,
                  m.mentorship_status, m.notes, m.skills
           FROM mentorship m
           WHERE m.mentor_id = ? AND m.status = 'active'
           ORDER BY m.id""",
        (root_id,)
    ).fetchall()

    apprentices = []
    for ar in apprentices_rows:
        sub_tree = build_tree(ar['apprentice_id'], visited.copy())
        if sub_tree:
            sub_tree['relation_id'] = ar['id']
            sub_tree['relationship_type'] = ar['relationship_type']
            sub_tree['start_date'] = ar['start_date']
            sub_tree['mentorship_status'] = ar['mentorship_status']
            sub_tree['skills'] = ar['skills']
            sub_tree['notes'] = ar['notes']
            apprentices.append(sub_tree)

    return {
        'user': user_info,
        'apprentices': apprentices
    }


# ============================================
# API 路由
# ============================================

@mentorship_bp.route('/list', methods=['GET'])
def list_mentorship():
    """获取所有师徒关系列表（带用户信息）"""
    db = get_db()
    rows = db.execute(
        """SELECT m.*,
                  mu.username as mentor_name, mu.shift_type as mentor_shift,
                  au.username as apprentice_name, au.shift_type as apprentice_shift
           FROM mentorship m
           LEFT JOIN users mu ON m.mentor_id = mu.id
           LEFT JOIN users au ON m.apprentice_id = au.id
           ORDER BY m.id DESC""",
    ).fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@mentorship_bp.route('/tree', methods=['GET'])
def get_tree():
    """获取完整的树状结构（所有顶层师傅作为根节点）"""
    db = get_db()

    # 找出所有顶层师傅：既是师傅但不是任何人的徒弟（status=active）
    all_mentors = db.execute(
        "SELECT DISTINCT mentor_id FROM mentorship WHERE status = 'active'"
    ).fetchall()
    all_apprentices = db.execute(
        "SELECT DISTINCT apprentice_id FROM mentorship WHERE status = 'active'"
    ).fetchall()

    mentor_ids = set(r['mentor_id'] for r in all_mentors)
    apprentice_ids = set(r['apprentice_id'] for r in all_apprentices)

    # 顶层师傅 = 有徒弟但自己不是任何人徒弟的人
    root_ids = mentor_ids - apprentice_ids

    # 如果没有师傅-徒弟关系被识别到，就把所有有徒弟的师傅作为根
    if not root_ids:
        root_ids = mentor_ids

    # 如果仍然没有根节点，显示所有用户作为独立节点（方便添加关系）
    trees = []
    for root_id in root_ids:
        tree = build_tree(root_id)
        if tree:
            trees.append(tree)

    return jsonify({
        'trees': trees,
        'total_relations': len(db.execute(
            "SELECT * FROM mentorship WHERE status = 'active'"
        ).fetchall()),
        'total_mentors': len(mentor_ids),
        'total_apprentices': len(apprentice_ids)
    })


@mentorship_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_mentorship(user_id):
    """获取某个用户的完整师徒关系（向上找师傅+向下找徒弟）"""
    db = get_db()
    user_info = get_user_info(user_id)
    if not user_info:
        return jsonify({'error': '用户不存在'}), 404

    # 找我的师傅们（向上）
    mentors_rows = db.execute(
        """SELECT m.*, u.username as mentor_name, u.shift_type as mentor_shift
           FROM mentorship m
           LEFT JOIN users u ON m.mentor_id = u.id
           WHERE m.apprentice_id = ? AND m.status = 'active'
           ORDER BY m.id""",
        (user_id,)
    ).fetchall()

    # 找我的徒弟们（向下）
    apprentices_rows = db.execute(
        """SELECT m.*, u.username as apprentice_name, u.shift_type as apprentice_shift
           FROM mentorship m
           LEFT JOIN users u ON m.apprentice_id = u.id
           WHERE m.mentor_id = ? AND m.status = 'active'
           ORDER BY m.id""",
        (user_id,)
    ).fetchall()

    # 构建向上的传承链路（递归找师傅的师傅）
    def build_upward(uid, visited=None):
        if visited is None:
            visited = set()
        if uid in visited:
            return []
        visited.add(uid)
        rows = db.execute(
            "SELECT mentor_id FROM mentorship WHERE apprentice_id = ? AND status = 'active'",
            (uid,)
        ).fetchall()
        result = []
        for r in rows:
            info = get_user_info(r['mentor_id'])
            if info:
                result.append({
                    'user': info,
                    'higher': build_upward(r['mentor_id'], visited.copy())
                })
        return result

    # 构建向下的传承链路（递归找徒弟的徒弟）
    def build_downward(uid, visited=None):
        if visited is None:
            visited = set()
        if uid in visited:
            return []
        visited.add(uid)
        rows = db.execute(
            "SELECT apprentice_id FROM mentorship WHERE mentor_id = ? AND status = 'active'",
            (uid,)
        ).fetchall()
        result = []
        for r in rows:
            info = get_user_info(r['apprentice_id'])
            if info:
                result.append({
                    'user': info,
                    'lower': build_downward(r['apprentice_id'], visited.copy())
                })
        return result

    return jsonify({
        'user': user_info,
        'mentors': [row_to_dict(r) for r in mentors_rows],
        'apprentices': [row_to_dict(r) for r in apprentices_rows],
        'upward_lineage': build_upward(user_id),
        'downward_lineage': build_downward(user_id)
    })


@mentorship_bp.route('/lineage/<int:user_id>', methods=['GET'])
def get_lineage(user_id):
    """获取某个员工的完整传承链路（从最顶层师傅到最底层徒弟）

    返回的链路中，每个关系节点都会包含 skills 字段，
    方便前端在展示"传承链路"时一并显示岗位技能。
    """
    db = get_db()
    user_info = get_user_info(user_id)
    if not user_info:
        return jsonify({'error': '用户不存在'}), 404

    # 递归向上找所有祖先路径（并记录 skills）
    def find_paths_up(uid, current_path, visited):
        if uid in visited:
            return [current_path] if len(current_path) > 1 else []
        visited.add(uid)
        mentors = db.execute(
            "SELECT mentor_id, skills FROM mentorship WHERE apprentice_id = ? AND status = 'active'",
            (uid,)
        ).fetchall()
        if not mentors:
            return [current_path] if len(current_path) > 1 else []
        paths = []
        for m in mentors:
            info = get_user_info(m['mentor_id'])
            if info:
                # 在当前用户（徒弟）信息中注入从师傅到此徒弟关系的 skills
                info_with_skills = dict(info)
                info_with_skills['skills_from_mentor'] = m['skills'] or ''
                sub_paths = find_paths_up(
                    m['mentor_id'],
                    [info_with_skills] + current_path,
                    visited.copy()
                )
                paths.extend(sub_paths)
        return paths

    # 递归向下找所有后代路径
    def find_paths_down(uid, current_path, visited):
        if uid in visited:
            return [current_path] if len(current_path) > 1 else []
        visited.add(uid)
        apprentices = db.execute(
            "SELECT apprentice_id, skills FROM mentorship WHERE mentor_id = ? AND status = 'active'",
            (uid,)
        ).fetchall()
        if not apprentices:
            return [current_path] if len(current_path) > 1 else []
        paths = []
        for a in apprentices:
            info = get_user_info(a['apprentice_id'])
            if info:
                info_with_skills = dict(info)
                info_with_skills['skills_from_mentor'] = a['skills'] or ''
                sub_paths = find_paths_down(
                    a['apprentice_id'],
                    current_path + [info_with_skills],
                    visited.copy()
                )
                paths.extend(sub_paths)
        return paths

    # 获取从最顶层祖先到该员工的路径
    up_paths = find_paths_up(user_id, [dict(user_info)], set())
    # 获取从该员工到最底层徒弟的路径
    down_paths = find_paths_down(user_id, [dict(user_info)], set())

    # 组合完整链路：up_path 的最后是当前用户，down_path 的第一个是当前用户
    full_lines = []
    for up in up_paths:
        for down in down_paths:
            full = up + down[1:]  # 去掉重复的当前用户
            if len(full) > 1:
                full_lines.append(full)

    # 如果没有找到完整链路，至少显示当前用户
    if not full_lines:
        full_lines = [[user_info]]

    return jsonify({
        'user': user_info,
        'lines': full_lines,
        'total_lines': len(full_lines)
    })


@mentorship_bp.route('', methods=['POST'])
@mentorship_bp.route('/', methods=['POST'])
def add_mentorship():
    """添加师徒关系"""
    data = request.get_json() or {}
    mentor_id = data.get('mentor_id')
    apprentice_id = data.get('apprentice_id')

    if not mentor_id or not apprentice_id:
        return jsonify({'error': '缺少必要参数: mentor_id 或 apprentice_id'}), 400

    if int(mentor_id) == int(apprentice_id):
        return jsonify({'error': '师傅和徒弟不能是同一个人'}), 400

    db = get_db()

    # 检查用户是否存在
    if not get_user_info(mentor_id):
        return jsonify({'error': '师傅不存在'}), 404
    if not get_user_info(apprentice_id):
        return jsonify({'error': '徒弟不存在'}), 404

    # 检查是否已存在相同关系（检查所有状态，包括已删除的）
    existing = db.execute(
        "SELECT * FROM mentorship WHERE mentor_id = ? AND apprentice_id = ?",
        (mentor_id, apprentice_id)
    ).fetchone()
    if existing:
        if existing['status'] == 'active':
            return jsonify({'error': '该师徒关系已存在'}), 400
        else:
            # 之前有软删除的记录，重新激活它
            db.execute(
                "UPDATE mentorship SET status = 'active', updated_at = ? WHERE id = ?",
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), existing['id'])
            )
            db.commit()
            return jsonify({
                'id': existing['id'],
                'mentor_id': mentor_id,
                'apprentice_id': apprentice_id,
                'message': '师徒关系已重新激活'
            })

    # 检查是否反向关系（避免 A->B 同时 B->A）
    reverse = db.execute(
        "SELECT * FROM mentorship WHERE mentor_id = ? AND apprentice_id = ?",
        (apprentice_id, mentor_id)
    ).fetchone()
    if reverse:
        return jsonify({'error': '已存在反向师徒关系'}), 400

    # 插入新关系（用 try/except 捕获唯一约束冲突，确保返回友好错误）
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_date = data.get('start_date') or datetime.now().strftime('%Y-%m-%d')
    relationship_type = data.get('relationship_type', 'direct')
    skills = data.get('skills', '')
    notes = data.get('notes', '')

    try:
        cursor = db.execute(
            """INSERT INTO mentorship
               (mentor_id, apprentice_id, relationship_type, start_date, status,
                notes, skills, mentorship_status, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'active', ?, ?, 'learning', ?, ?)""",
            (mentor_id, apprentice_id, relationship_type, start_date,
             notes, skills, now, now)
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        return jsonify({'error': '师徒关系已存在（唯一约束冲突）'}), 400

    return jsonify({
        'id': cursor.lastrowid,
        'mentor_id': mentor_id,
        'apprentice_id': apprentice_id,
        'skills': skills,
        'message': '师徒关系添加成功'
    })


@mentorship_bp.route('/<int:relation_id>', methods=['DELETE'])
def delete_mentorship(relation_id):
    """删除师徒关系（软删除：将 status 改为 deleted）"""
    db = get_db()
    relation = db.execute(
        "SELECT * FROM mentorship WHERE id = ?",
        (relation_id,)
    ).fetchone()
    if not relation:
        return jsonify({'error': '师徒关系不存在'}), 404

    db.execute(
        "UPDATE mentorship SET status = 'deleted', updated_at = ? WHERE id = ?",
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), relation_id)
    )
    db.commit()

    return jsonify({'message': '师徒关系已删除', 'id': relation_id})


@mentorship_bp.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user_mentorship(user_id):
    """删除某用户作为师傅的所有师徒关系（用于移除根节点，徒弟将成为新根节点）"""
    db = get_db()

    # 先检查用户是否存在
    if not get_user_info(user_id):
        return jsonify({'error': '用户不存在'}), 404

    # 查找该用户作为师傅的所有关系
    relations = db.execute(
        "SELECT id, apprentice_id FROM mentorship WHERE mentor_id = ? AND status = 'active'",
        (user_id,)
    ).fetchall()

    if not relations:
        return jsonify({
            'message': '该用户没有徒弟关系需要删除',
            'deleted_count': 0
        })

    # 软删除所有关系
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for r in relations:
        db.execute(
            "UPDATE mentorship SET status = 'deleted', updated_at = ? WHERE id = ?",
            (now, r['id'])
        )
    db.commit()

    return jsonify({
        'message': f'已移除该用户作为师傅的 {len(relations)} 条师徒关系',
        'deleted_count': len(relations),
        'apprentice_ids': [r['apprentice_id'] for r in relations]
    })


@mentorship_bp.route('/<int:relation_id>', methods=['PUT'])
def update_mentorship(relation_id):
    """更新师徒关系信息"""
    data = request.get_json() or {}
    db = get_db()

    relation = db.execute(
        "SELECT * FROM mentorship WHERE id = ?",
        (relation_id,)
    ).fetchone()
    if not relation:
        return jsonify({'error': '师徒关系不存在'}), 404

    # 更新可修改字段
    fields = {
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'skills': data.get('skills'),
        'notes': data.get('notes'),
        'mentorship_status': data.get('mentorship_status'),
        'qualification': data.get('qualification'),
    }

    # 过滤掉 None 值
    updates = {k: v for k, v in fields.items() if v is not None}

    if not updates:
        return jsonify({'message': '没有需要更新的字段'})

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), relation_id]

    db.execute(f"UPDATE mentorship SET {set_clause}, updated_at = ? WHERE id = ?", params)
    db.commit()

    return jsonify({'message': '师徒关系已更新', 'id': relation_id})


@mentorship_bp.route('/users/search', methods=['GET'])
def search_users():
    """搜索员工（用于添加师徒关系时选择）

    支持三种匹配方式：
    1. 用户名中包含关键词（模糊匹配）
    2. 员工编号/角色中包含关键词
    3. 中文拼音首字母匹配（例如 "zsf" 匹配 "张三峰"）
    """
    keyword = request.args.get('q', '').strip()
    exclude = request.args.get('exclude', '')  # 逗号分隔的排除ID列表
    exclude_ids = []
    if exclude:
        try:
            exclude_ids = [int(x) for x in exclude.split(',') if x.strip()]
        except ValueError:
            exclude_ids = []

    db = get_db()

    # 基础查询条件（未登录时全部员工）
    if keyword:
        query = """SELECT id, username, shift_type, is_active, hire_date, role, employee_id
                   FROM users
                   WHERE is_active = 1
                   ORDER BY id ASC"""
        rows = db.execute(query).fetchall()

        # 1) 先用 SQL LIKE 过滤：包含关键词的
        # 2) 再在 Python 中进行拼音首字母匹配
        keyword_upper = keyword.upper()
        is_ascii = bool(keyword) and all(
            (ord(c) < 128) and c.isalpha() for c in keyword_upper
        )

        results = []
        for r in rows:
            if r['id'] in exclude_ids:
                continue

            username = r['username'] or ''
            role = r['role'] or ''
            emp_id = r['employee_id'] or ''

            matched = False
            # 直接包含关键词（不区分大小写）
            if (keyword_upper in username.upper() or
                    keyword_upper in emp_id.upper() or
                    keyword_upper in role.upper()):
                matched = True

            # 拼音首字母匹配（仅在关键词为纯英文字母时）
            if not matched and is_ascii:
                username_initials = get_pinyin_initials(username)
                role_initials = get_pinyin_initials(role)
                if (keyword_upper in username_initials or
                        keyword_upper in role_initials or
                        username_initials.startswith(keyword_upper)):
                    matched = True

            if matched:
                results.append({
                    'id': r['id'],
                    'username': username,
                    'shift_type': r['shift_type'],
                    'role': role,
                    'pinyin_initials': get_pinyin_initials(username)
                })
                if len(results) >= 100:
                    break
    else:
        query = """SELECT id, username, shift_type, is_active, hire_date, role
                   FROM users WHERE is_active = 1
                   ORDER BY id ASC
                   LIMIT 100"""
        rows = db.execute(query).fetchall()
        results = []
        for r in rows:
            if r['id'] in exclude_ids:
                continue
            results.append({
                'id': r['id'],
                'username': r['username'],
                'shift_type': r['shift_type'],
                'role': r['role'],
                'pinyin_initials': get_pinyin_initials(r['username'] or '')
            })

    return jsonify({
        'count': len(results),
        'users': results
    })
