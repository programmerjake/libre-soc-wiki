#!/usr/bin/env python

from copy import deepcopy

def pins(pingroup, bankspec, suffix, offs, bank, mux, spec=None, limit=None):
    res = {}
    names = {}
    idx = 0
    for name in pingroup[:limit]:
        if suffix:
            name_ = "%s_%s" % (name, suffix)
        else:
            name_ = name
        if spec and spec.has_key(name):
            continue
        pin = {mux: (name_, bank)}
        offs_bank, offs_ = offs
        idx_ = offs_ + idx
        idx += 1
        idx_ += bankspec[bank]
        res[idx_] = pin
        names[name] = idx_
    for name in pingroup:
        if suffix:
            name_ = "%s_%s" % (name, suffix)
        else:
            name_ = name
        if not spec:
            continue
        if not spec.has_key(name):
            continue
        idx_, mux_, bank_ = spec[name]
        idx_ = names[idx_]
        #idx_ += bankspec[bank_]
        pin = {mux_: (name_, bank_)}
        if res.has_key(idx_):
            res[idx_].update(pin)
        else:
            res[idx_] = pin
    return res

def i2s(bankspec, suffix, offs, bank, mux=1, spec=None, limit=None):
    i2spins = ['IISMCK', 'IISBCK', 'IISLRCK', 'IISDI']
    for i in range(4):
        i2spins.append("IISDO%d" % i)
    return pins(i2spins, bankspec, suffix, offs, bank, mux, spec, limit)

def emmc(bankspec, suffix, offs, bank, mux=1, spec=None):
    emmcpins = ['MMCCMD', 'MMCCLK']
    for i in range(8):
        emmcpins.append("MMCD%d" % i)
    return pins(emmcpins, bankspec, suffix, offs, bank, mux, spec)

def sdmmc(bankspec, suffix, offs, bank, mux=1, spec=None,
                start=None, limit=None):
    sdmmcpins = ['CMD', 'CLK']
    for i in range(4):
        sdmmcpins.append("D%d" % i)
    sdmmcpins = sdmmcpins[start:limit]
    sdmmcpins = namesuffix('SD', suffix, sdmmcpins)
    return pins(sdmmcpins, bankspec, '', offs, bank, mux, spec)

def spi(bankspec, suffix, offs, bank, mux=1, spec=None):
    spipins = namesuffix('SPI', suffix,
                ['CLK', 'NSS', 'MOSI', 'MISO', 'NSS'])
    return pins(spipins, bankspec, '', offs, bank, mux, spec)

def quadspi(bankspec, suffix, offs, bank, mux=1, spec=None, limit=None):
    spipins = namesuffix('SPI', suffix,
                ['CK', 'NSS', 'IO0', 'IO1', 'IO2', 'IO3'])
    return pins(spipins, bankspec, '', offs, bank, mux, spec, limit)

def i2c(bankspec, suffix, offs, bank, mux=1, spec=None):
    spipins = namesuffix('TWI', suffix,
                ['SDA', 'SCL'])
    return pins(spipins, bankspec, '', offs, bank, mux, spec)

def jtag(bankspec, suffix, offs, bank, mux=1, spec=None):
    uartpins = namesuffix('JTAG', suffix, ['MS', 'DI', 'DO', 'CK'])
    return pins(uartpins, bankspec, '', offs, bank, mux, spec)

def uart(bankspec, suffix, offs, bank, mux=1, spec=None):
    uartpins = namesuffix('UART', suffix, ['TX', 'RX'])
    return pins(uartpins, bankspec, '', offs, bank, mux, spec)

def namesuffix(name, suffix, namelist):
    names = []
    for n in namelist:
        names.append("%s%s_%s" % (name, suffix, n))
    return names

def ulpi(bankspec, suffix, offs, bank, mux=1, spec=None):
    ulpipins = namesuffix('ULPI', suffix, ['CK', 'DIR', 'STP', 'NXT'])
    for i in range(8):
        ulpipins.append('ULPI%s_D%d' % (suffix, i))
    return pins(ulpipins, bankspec, "", offs, bank, mux, spec)

def uartfull(bankspec, suffix, offs, bank, mux=1, spec=None):
    uartpins = namesuffix('UART', suffix, ['TX', 'RX', 'CTS', 'RTS'])
    return pins(uartpins, bankspec, '', offs, bank, mux, spec)

def rgbttl(bankspec, suffix, offs, bank, mux=1, spec=None):
    ttlpins = ['LCDCK', 'LCDDE', 'LCDHS', 'LCDVS']
    for i in range(24):
        ttlpins.append("LCD%d" % i)
    return pins(ttlpins, bankspec, suffix, offs, bank, mux, spec)

def rgmii(bankspec, suffix, offs, bank, mux=1, spec=None):
    buspins = []
    for i in range(4):
        buspins.append("RG_ERXD%d" % i)
    for i in range(4):
        buspins.append("RG_ETXD%d" % i)
    for i in range(2):
        buspins.append("RG_FB_CS%d" % i)
    buspins += ['RG_ERXCK', 'RG_ERXERR', 'RG_ERXDV',
                'RG_EMDC', 'RG_EMDIO',
                'RG_ETXEN', 'RG_ETXCK', 'RG_ECRS',
                'RG_ECOL', 'RG_ETXERR']
    return pins(buspins, bankspec, suffix, offs, bank, mux, spec)

def flexbus1(bankspec, suffix, offs, bank, mux=1, spec=None, limit=None):
    buspins = []
    for i in range(8):
        buspins.append("FB_AD%d" % i)
    for i in range(2):
        buspins.append("FB_CS%d" % i)
    buspins += ['FB_ALE', 'FB_OE', 'FB_RW', 'FB_TA', 'FB_CLK',
                'FB_A0', 'FB_A1', 'FB_TS', 'FB_TBST',
                'FB_TSIZ0', 'FB_TSIZ1']
    for i in range(4):
        buspins.append("FB_BWE%d" % i)
    for i in range(2,6):
        buspins.append("FB_CS%d" % i)
    return pins(buspins, bankspec, suffix, offs, bank, mux, spec, limit)

def flexbus2(bankspec, suffix, offs, bank, mux=1, spec=None, limit=None):
    buspins = []
    for i in range(8,32):
        buspins.append("FB_AD%d" % i)
    return pins(buspins, bankspec, suffix, offs, bank, mux, spec, limit)

def mcu8080(bankspec, suffix, offs, bank, mux=1, spec=None):
    buspins = []
    for i in range(8):
        buspins.append("MCUD%d" % i)
    for i in range(8):
        buspins.append("MCUAD%d" % (i+8))
    for i in range(6):
        buspins.append("MCUCS%d" % i)
    for i in range(2):
        buspins.append("MCUNRB%d" % i)
    buspins += ['MCUCD', 'MCURD', 'MCUWR', 'MCUCLE', 'MCUALE',
                'MCURST']
    return pins(buspins, bankspec, suffix, offs, bank, mux, spec)

def _pinbank(bankspec, prefix, suffix, offs, bank, gpiooffs, gpionum=1, mux=1, spec=None):
    gpiopins = []
    for i in range(gpiooffs, gpiooffs+gpionum):
        gpiopins.append("%s%s%d" % (prefix, bank, i))
    return pins(gpiopins, bankspec, suffix, offs, bank, mux, spec)

def eint(bankspec, suffix, offs, bank, gpiooffs, gpionum=1, mux=1, spec=None):
    gpiopins = []
    for i in range(gpiooffs, gpiooffs+gpionum):
        gpiopins.append("EINT%d" % (i))
    return pins(gpiopins, bankspec, suffix, offs, bank, mux, spec)

def pwm(bankspec, suffix, offs, bank, mux=1, spec=None):
    return pins(['PWM', ], bankspec, suffix, offs, bank, mux, spec)

def gpio(bankspec, suffix, offs, bank, gpiooffs, gpionum=1, mux=1, spec=None):
    return _pinbank(bankspec, "GPIO", suffix, offs, bank, gpiooffs,
                              gpionum, mux=0, spec=None)

def display(pins):
    print "| Pin | Mux0        | Mux1        | Mux2        | Mux3        |"
    print "| --- | ----------- | ----------- | ----------- | ----------- |"
    pinidx = pins.keys()
    pinidx.sort()
    for pin in pinidx:
        pdata = pins[pin]
        res = '| %3d |' % pin
        for mux in range(4):
            if not pdata.has_key(mux):
                res += "             |"
                continue
            name, bank = pdata[mux]
            res += " %s %-9s |" % (bank, name)
        print res

def fnsplit(f):
    a = ''
    n = 0
    if not f.startswith('FB_'):
        f2 = f.split('_')
        if len(f2) == 2:
            if f2[1].isdigit():
                return f2[0], int(f2[1])
            return f2[0], f2[1]
    #print f
    while f and not f[0].isdigit():
        a += f[0]
        f = f[1:]
    return a, int(f) if f else None

def fnsort(f1, f2):
    a1, n1 = fnsplit(f1)
    a2, n2 = fnsplit(f2)
    x = cmp(a1, a2)
    if x != 0:
        return x
    return cmp(n1, n2)
    
def find_fn(fname, names):
    for n in names:
        if fname.startswith(n):
            return n

def display_fns(bankspec, pins, function_names):
    fn_names = function_names.keys()
    fns = {}
    for (pin, pdata) in pins.items():
        for mux in range(1,4): # skip GPIO for now
            if not pdata.has_key(mux):
                continue
            name, bank = pdata[mux]
            if not fns.has_key(name):
                fns[name] = []
            fns[name].append((pin-bankspec[bank], mux, bank))

    fnidx = fns.keys()
    fnidx.sort(fnsort)
    current_fn = None
    for fname in fnidx:
        fnbase = find_fn(fname, fn_names)
        #print "name", fname
        if fnbase != current_fn:
            if current_fn is not None:
                print
            print "## %s" % fnbase
            print
            print function_names[fnbase]
            print
            current_fn = fnbase
        print "* %-9s :" % fname,
        for (pin, mux, bank) in fns[fname]:
            print "%s%d/%d" % (bank, pin, mux),
        print

    return fns

def check_functions(title, bankspec, fns, pins, required, eint, pwm,
                    descriptions=None):
    fns = deepcopy(fns)
    pins = deepcopy(pins)
    if descriptions is None:
        descriptions = {}

    print "# Pinmap for %s" % title
    print


    for name in required:
        print "## %s" % name
        print
        if descriptions and descriptions.has_key(name):
            print descriptions[name]
            print

        name = name.split(':')
        if len(name) == 2:
            findbank = name[0][0]
            findmux = int(name[0][1:])
            name = name[1]
        else:
            name = name[0]
            findbank = None
            findmux = None
        name = name.split('/')
        if len(name) == 2:
            count = int(name[1])
        else:
            count = 100000
        name = name[0]
        found = set()
        fnidx = fns.keys()
        #fnidx.sort(fnsort)
        pinfound = {}
        for fname in fnidx:
            if not fname.startswith(name):
                continue
            for pin, mux, bank in fns[fname]:
                if findbank is not None:
                    if findbank != bank:
                        continue
                    if findmux != mux:
                        continue
                pin_ = pin + bankspec[bank]
                if pins.has_key(pin_):
                    pinfound[pin_] = (fname, pin_, bank, pin, mux)

        pinidx = pinfound.keys()
        pinidx.sort()

        for pin_ in pinidx:
            fname, pin_, bank, pin, mux = pinfound[pin_]
            if fname in found:
                continue
            found.add(fname)
            if len(found) > count:
                continue
            del pins[pin_]
            print "* %s %d %s%d/%d" % (fname, pin_, bank, pin, mux)

        print

    # gpios
    gpios = []
    for name in descriptions.keys():
        if not name.startswith('GPIO'):
            continue
        if name == 'GPIO':
            continue
        gpios.append(name)
    gpios.sort()
    
    if gpios:
        print "## GPIO"
        print

        for fname in gpios:
            if fname in found:
                continue
            desc = ''
            if descriptions and descriptions.has_key(fname):
                desc = ': %s' % descriptions[fname]
            bank = fname[4]
            pin = int(fname[5:])
            pin_ = pin + bankspec[bank]
            if not pins.has_key(pin_):
                continue
            del pins[pin_]
            found.add(fname)
            print "* %-8s %d %s%-2d %s" % (fname, pin_, bank, pin, desc)
        print

    if eint:
        display_group("EINT", eint, fns, pins, descriptions)
    if pwm:
        display_group("PWM", pwm, fns, pins, descriptions)

    print "## Unused Pinouts (spare as GPIO) for '%s'" % title
    print
    if descriptions and descriptions.has_key('GPIO'):
        print descriptions['GPIO']
        print 
    display(pins)
    print

    return pins # unused

def display_group(title, todisplay, fns, pins, descriptions):
    print "## %s" % title
    print

    found = set()
    for fname in todisplay:
        desc = ''
        if descriptions and descriptions.has_key(fname):
            desc = ': %s' % descriptions[fname]
        fname = fname.split(':')
        if len(fname) == 2:
            findbank = fname[0][0]
            findmux = int(fname[0][1:])
            fname = fname[1]
        else:
            fname = fname[0]
            findbank = None
            findmux = None
        for (pin, mux, bank) in fns[fname]:
            if findbank is not None:
                if findbank != bank:
                    continue
                if findmux != mux:
                    continue
            if fname in found:
                continue
            pin_ = pin + bankspec[bank]
            if not pins.has_key(pin_):
                continue
            del pins[pin_]
            found.add(fname)
            print "* %s %d %s%d/%d %s" % (fname, pin_, bank, pin, mux, desc)
    print

def pinmerge(pins, fn):
    for (pinidx, v) in fn.items():
        if not pins.has_key(pinidx):
            pins[pinidx] = v
            continue
        pins[pinidx].update(v)

def display_fixed(fixed, offs):

    fkeys = fixed.keys()
    fkeys.sort()
    pin_ = offs
    for pin, k in enumerate(fkeys):
        print "## %s" % k
        print
        prevname = ''
        linecount = 0
        for name in fixed[k]:
            if linecount == 4:
                linecount = 0
                print
            if prevname[:2] == name[:2] and linecount != 0:
                print name,
                linecount += 1
            else:
                if linecount != 0:
                    print
                print "* %d: %d %s" % (pin_, pin, name),
                linecount = 1
            prevname = name
            pin_ += 1
        if linecount != 0:
            print
        print

if __name__ == '__main__':
    pinouts = {}

    pinbanks = {'A': 16,
                'B': 16,
                'C': 16,
                'D': 16,
                'E': 48,
              }
    bankspec = {}
    pkeys = pinbanks.keys()
    pkeys.sort()
    offs = 0
    for kn in pkeys:
        bankspec[kn] = offs
        offs += pinbanks[kn]

    # Bank A, 0-15
    pinmerge(pinouts, gpio(bankspec, "", ('A', 0), "A", 0, 16, 0))
    pinmerge(pinouts, spi(bankspec, "0", ('A', 0), "A", 1))
    pinmerge(pinouts, spi(bankspec, "1", ('A', 4), "A", 1))
    pinmerge(pinouts, uart(bankspec, "0", ('A', 8), "A", 1))
    pinmerge(pinouts, uart(bankspec, "1", ('A', 10), "A", 1))
    pinmerge(pinouts, i2c(bankspec, "0", ('A', 12), "A", 1))
    pinmerge(pinouts, i2c(bankspec, "1", ('A', 14), "A", 1))
    for i in range(16):
        pinmerge(pinouts, pwm(bankspec, str(i), ('A', i), "A", mux=2))

    # Bank B, 16-31
    pinmerge(pinouts, gpio(bankspec, "", ('B', 0), "B", 0, 16, 0))
    pinmerge(pinouts, spi(bankspec, "2", ('B', 0), "B", 1))
    pinmerge(pinouts, uart(bankspec, "2", ('B', 4), "B", 1))
    pinmerge(pinouts, uart(bankspec, "3", ('B', 6), "B", 1))
    pinmerge(pinouts, uart(bankspec, "4", ('B', 8), "B", 1))
    pinmerge(pinouts, i2c(bankspec, "2", ('B', 10), "B", 1))
    pinmerge(pinouts, i2c(bankspec, "3", ('B', 12), "B", 1))
    pinmerge(pinouts, uart(bankspec, "5", ('B', 14), "B", 1))
    for i in range(16):
        pinmerge(pinouts, pwm(bankspec, str(i+16), ('B', i), "B", mux=2))

    # Bank C, 32-47
    pinmerge(pinouts, ulpi(bankspec, "0", ('C', 0), "C", 1))
    pinmerge(pinouts, spi(bankspec, "0", ('C', 12), "C", 1))

    # Bank D, 48-64
    pinmerge(pinouts, sdmmc(bankspec, "0", ('D', 0), "D", 1))
    pinmerge(pinouts, jtag(bankspec, "0", ('D', 6), "D", 1))
    pinmerge(pinouts, uart(bankspec, "0", ('D', 10), "D", 1))
    pinmerge(pinouts, i2c(bankspec, "0", ('D', 12), "D", 1))
    pinmerge(pinouts, uart(bankspec, "1", ('D', 14), "D", 1))

    # Bank E, 64-111
    flexspec = {
        'FB_TS': ('FB_ALE', 2, "D"),
        'FB_CS2': ('FB_BWE2', 2, "D"),
        'FB_A0': ('FB_BWE2', 3, "D"),
        'FB_CS3': ('FB_BWE3', 2, "D"),
        'FB_A1': ('FB_BWE3', 3, "D"),
        'FB_TBST': ('FB_OE', 2, "D"),
        'FB_TSIZ0': ('FB_BWE0', 2, "D"),
        'FB_TSIZ1': ('FB_BWE1', 2, "D"),
    }
    pinmerge(pinouts, flexbus1(bankspec, "", ('E', 0), "E", 1))
    pinmerge(pinouts, flexbus2(bankspec, "", ('E', 30), "E", 1, limit=8))

    print "# Pinouts (PinMux)"
    print
    print "auto-generated by [[pinouts.py]]"
    print
    print "[[!toc  ]]"
    print
    display(pinouts)
    print

    print "# Pinouts (Fixed function)"
    print

    fixedpins = {
      'CTRL_SYS':
        [
        'TEST', 'BOOT_SEL', 
        'NMI#', 'RESET#', 
        'CLK24M_IN', 'CLK24M_OUT', 
        'CLK32K_IN', 'CLK32K_OUT', 
        'PLLTEST', 'PLLREGIO', 'PLLVP25', 
        'PLLDV', 'PLLVREG', 'PLLGND', 
       ],

      'POWER_CPU':
        ['VDD0_CPU', 'VDD1_CPU', 'VDD2_CPU', 'VDD3_CPU', 'VDD4_CPU', 'VDD5_CPU',
         'GND0_CPU', 'GND1_CPU', 'GND2_CPU', 'GND3_CPU', 'GND4_CPU', 'GND5_CPU',
        ],

      'POWER_DLL':
        ['VDD0_DLL', 'VDD1_DLL', 'VDD2_DLL', 
         'GND0_DLL', 'GND1_DLL', 'GND2_DLL', 
        ],

      'POWER_INT':
        ['VDD0_INT', 'VDD1_INT', 'VDD2_INT', 'VDD3_INT', 'VDD4_INT', 
         'VDD5_INT', 'VDD6_INT', 'VDD7_INT', 'VDD8_INT', 'VDD9_INT', 
         'GND0_INT', 'GND1_INT', 'GND2_INT', 'GND3_INT', 'GND4_INT', 
         'GND5_INT', 'GND6_INT', 'GND7_INT', 'GND8_INT', 'GND9_INT', 
        ],

      'POWER_GPIO':
        ['VDD_GPIOA', 'VDD_GPIOB', 'VDD_GPIOC', 'VDD_GPIOD', 'VDD_GPIOE',
         'GND_GPIOA', 'GND_GPIOB', 'GND_GPIOC', 'GND_GPIOD', 'GND_GPIOE',
        ]

      }

    display_fixed(fixedpins, len(pinouts))

    print "# Functions (PinMux)"
    print
    print "auto-generated by [[pinouts.py]]"
    print

    function_names = {'EINT': 'External Interrupt',
                      'FB': 'MC68k FlexBus',
                      'IIS': 'I2S Audio',
                      'JTAG0': 'JTAG',
                      'JTAG1': 'JTAG (same as JTAG2, JTAG_SEL=LOW)',
                      'JTAG2': 'JTAG (same as JTAG1, JTAG_SEL=HIGH)',
                      'LCD': '24-pin RGB/TTL LCD',
                      'RG': 'RGMII Ethernet',
                      'MMC': 'eMMC 1/2/4/8 pin',
                      'PWM': 'PWM (pulse-width modulation)',
                      'SD0': 'SD/MMC 0',
                      'SD1': 'SD/MMC 1',
                      'SD2': 'SD/MMC 2',
                      'SD3': 'SD/MMC 3',
                      'SPI0': 'SPI (Serial Peripheral Interface) 0',
                      'SPI1': 'SPI (Serial Peripheral Interface) 1',
                      'SPI2': 'SPI (Serial Peripheral Interface) 2',
                      'SPI3': 'Quad SPI (Serial Peripheral Interface) 3',
                      'TWI0': 'I2C 0',
                      'TWI1': 'I2C 1',
                      'TWI2': 'I2C 2',
                      'TWI3': 'I2C 3',
                      'UART0': 'UART (TX/RX) 0',
                      'UART1': 'UART (TX/RX) 1',
                      'UART2': 'UART (TX/RX) 2',
                      'UART3': 'UART (TX/RX) 3',
                      'UART4': 'UART (TX/RX) 4',
                      'UART5': 'UART (TX/RX) 5',
                      'ULPI0': 'ULPI (USB Low Pin-count) 0',
                      'ULPI1': 'ULPI (USB Low Pin-count) 1',
                      'ULPI2': 'ULPI (USB Low Pin-count) 2',
                      'ULPI3': 'ULPI (USB Low Pin-count) 3',
                    }
            
    fns = display_fns(bankspec, pinouts, function_names)
    print

    # Scenarios below can be spec'd out as either "find first interface"
    # by name/number e.g. SPI1, or as "find in bank/mux" which must be
    # spec'd as "BM:Name" where B is bank (A-F), M is Mux (0-3)
    # EINT and PWM are grouped together, specially, but may still be spec'd
    # using "BM:Name".  Pins are removed in-order as listed from
    # lists (interfaces, EINTs, PWMs) from available pins.

    # Robotics scenario.  

    robotics = ['FB', 'ULPI0/8', 
                'SD0',
                'JTAG0', 'D1:UART0', 
              'C1:SPI0', 'D1:TWI0']
    robotics_pwm = []
    for i in range(32):
        robotics_pwm.append('PWM_%d' % i)
    robotics_eint = ['EINT24', 'EINT25', 'EINT26', 'EINT27',
                       'EINT20', 'EINT21', 'EINT22', 'EINT23']
    robotics_eint = []

    unused_pins = check_functions("Robotics", bankspec, fns, pinouts,
                 robotics, robotics_eint, robotics_pwm)

    print "# Reference Datasheets"
    print
    print "datasheets and pinout links"
    print
    print "* <http://datasheets.chipdb.org/AMD/8018x/80186/amd-80186.pdf>"
    print "* <http://hands.com/~lkcl/eoma/shenzen/frida/FRD144A2701.pdf>"
    print "* <http://pinouts.ru/Memory/sdcard_pinout.shtml>"
    print "* p8 <http://www.onfi.org/~/media/onfi/specs/onfi_2_0_gold.pdf?la=en>"
    print "* <https://www.heyrick.co.uk/blog/files/datasheets/dm9000aep.pdf>"
    print "* <http://cache.freescale.com/files/microcontrollers/doc/app_note/AN4393.pdf>"
    print "* <https://www.nxp.com/docs/en/data-sheet/MCF54418.pdf>"
    print "* ULPI OTG PHY, ST <http://www.st.com/en/interfaces-and-transceivers/stulpi01a.html>"
    print "* ULPI OTG PHY, TI TUSB1210 <http://ti.com/product/TUSB1210/>"

