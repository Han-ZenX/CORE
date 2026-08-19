# XC7Z020 PL 侧时钟引脚说明

本文说明本工程所用器件 PL(FPGA)部分哪些引脚可以作为外部时钟输入,以及如何核实。

> 注意:文中列出的具体引脚编号未在本机经 Vivado 验证(本机无 Vivado 工具链),请按文末"核实方法"一节自行确认。规则部分(MRCC/SRCC 命名法、每 bank 4 对)是 7 系列架构的固定约定,可放心依据。

---

## 1. 器件与可用 I/O Bank

本工程器件:`xc7z020clg400-2`

CLG400 封装的 PL 侧只有两个 HR(High Range,1.2–3.3 V)I/O bank:

| Bank | 类型 | I/O 数 |
|------|------|--------|
| Bank 34 | HR | 50 |
| Bank 35 | HR | 50 |

CLG484 / FBG484 等更大封装才额外提供 Bank 13。因此本器件 PL 侧的时钟引脚全部落在 Bank 34 和 Bank 35 内。

---

## 2. 时钟引脚规则

Zynq-7000 的 PL 与 Artix/Kintex-7 同架构,**没有 Spartan-6 那种独立的专用 GCLK 引脚**。外部时钟必须从 "Clock Capable"(CC)引脚进入,通过引脚名中的标记识别:

| 标记 | 全称 | 能力 |
|------|------|------|
| `MRCC` | Multi-Region Clock Capable | 可驱动 BUFG(全局时钟树)、MMCM/PLL,以及**本 clock region 及上下相邻 region** 的 BUFIO / BUFR |
| `SRCC` | Single-Region Clock Capable | 可驱动 BUFG、MMCM/PLL,但 BUFIO / BUFR **仅限本 clock region** |

两者都能进全局时钟树,差别在于跨 region 驱动本地时钟缓冲(BUFIO/BUFR)的能力。**优先选 MRCC**。

### 每个 Bank 的固定 4 对

7 系列每个 I/O bank 都有且仅有 4 对(8 个)CC 引脚,物理位置在 bank 中部,命名固定为:

```
IO_L11P/N_T1_SRCC_<bank>
IO_L12P/N_T1_MRCC_<bank>
IO_L13P/N_T2_MRCC_<bank>
IO_L14P/N_T2_SRCC_<bank>
```

对本器件而言:

- PL 侧 CC 引脚总数:2 bank × 4 对 = **8 对 / 16 个引脚**
- 其中 MRCC 4 对(8 个)、SRCC 4 对(8 个)

差分时钟(如 LVDS)用 P/N 整对;单端时钟接 P 端即可,N 端可作普通 I/O。

### 常见板卡参考

以下为业界常见板卡上使用的对应关系,仅供交叉印证:

| 引脚 | 功能名 | 说明 |
|------|--------|------|
| U18 / U19 | `IO_L12P/N_T1_MRCC_34` | Bank 34 的 MRCC 对 |
| N18 / P19 | `IO_L13P/N_T2_MRCC_34` | Bank 34 的 MRCC 对 |
| K17 / K18 | `IO_L12P/N_T1_MRCC_35` | Bank 35 的 MRCC 对,Zybo Z7-20 的 125 MHz 时钟即接 K17 |
| H16 / H17 | `IO_L13P/N_T2_MRCC_35` | Bank 35 的 MRCC 对 |
| U14 / U15 | `IO_L11P/N_T2_SRCC_34` | Bank 34 的 SRCC 对 |
| N20 / P20 | `IO_L14P/N_T2_SRCC_34` | Bank 34 的 SRCC 对 |
| L16 / L17 | `IO_L11P/N_T2_SRCC_35` | Bank 35 的 SRCC 对 |
| J18 / H18 | `IO_L14P/N_T2_SRCC_35` | Bank 35 的 SRCC 对 |

---

## 3. 本工程当前使用情况

约束文件:`top_cymometer.srcs/constrs_1/new/top_cymometer.xdc`

| 端口 | 引脚 | 约束周期 | 类型 |
|------|------|----------|------|
| `clk_fs_p` | Y12 | 3.200 ns(312.5 MHz) | 差分 |
| `clk_fx_p` | B19 | 2.857 ns(350 MHz) | 差分 |
| `clk_10m` | V5 | 100.000 ns(10 MHz) | 单端 LVCMOS33 |

**这三个引脚是否落在 CC 引脚上,尚未确认。** 建议逐个核实:

- 若某个时钟输入不在 CC 引脚上,Vivado 布局阶段会报 `[Place 30-876]` 一类警告;
- 该时钟只能绕道普通逻辑布线才能进入 BUFG,会引入额外的插入延迟和抖动;
- 对本工程(测频 / TDC 进位链)而言,时钟质量直接影响测量精度,不宜将就。

---

## 4. 核实方法

### 方法一:Vivado Tcl Console(最直接)

打开工程后,在 Tcl Console 中列出所有 CC 引脚:

```tcl
foreach p [get_package_pins] {
    set s [get_property PIN_FUNC $p]
    if {[string match *RCC* $s]} { puts "$p  $s" }
}
```

或直接查询某个引脚的功能:

```tcl
get_property PIN_FUNC [get_package_pins Y12]
get_property PIN_FUNC [get_package_pins B19]
get_property PIN_FUNC [get_package_pins V5]
```

返回值中含 `MRCC` 或 `SRCC` 即为时钟引脚。

### 方法二:GUI

打开 I/O Planning 视图 → Package Pins 窗口 → 查看 **Pin Function** 列,按 `RCC` 过滤。

### 方法三:官方文档

查阅 UG865 *Zynq-7000 SoC Packaging and Pinout* 及其配套的 Package Pin CSV / `xc7z020clg400pkg.txt` 文件,内含全部引脚的完整功能名。

---

## 5. 选型建议

1. 外部时钟输入**必须**接 CC 引脚,不要接普通 I/O。
2. 优先选 MRCC 而非 SRCC,尤其是需要跨 region 分发或接 BUFR/BUFIO 时。
3. 时钟引脚所在 bank 的 VCCO 电平须与时钟源电平匹配(Bank 34 / 35 均为 HR bank,支持 1.2–3.3 V)。
4. 若需 MMCM/PLL 直接吃外部时钟,时钟引脚应与目标 MMCM 在同一或相邻 clock region,否则 Vivado 会插入额外的时钟缓冲。
