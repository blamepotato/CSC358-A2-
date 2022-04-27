from mininet.topo import Topo

class StraightRouter(Topo):
    """
        A multi-router network topology to test basic functionality of router broadcasting and advertising
        r1 = u  s1  h1
        r2 = v  s2  h2
        r3 = w  s3  h3
        r4 = x  s4  h4
        r5 = y  s5  h5
        The ip address of hosts and interfaces in this topology is static.
    """

    def __init__(self, **params):
        Topo.__init__(self)

        # Add hosts and switches
        # r1 network host
        r1 = self.addHost('r1', ip='10.1.0.1/24',
                          hostRoute='10.101.0.1 via 10.104.0.1')
        h1 = self.addHost('h1', ip='10.1.0.251/24')
        s1 = self.addSwitch('s1')

        # r2 network host
        r2 = self.addHost('r2', ip='10.101.0.1/24')
        h2 = self.addHost('h2', ip='10.101.0.251/24')
        s2 = self.addSwitch('s2')

        # r3 network host
        r3 = self.addHost('r3', ip='10.103.0.1/24')
        h3 = self.addHost('h3', ip="10.103.0.251/24")
        s3 = self.addSwitch('s3')

        # r4 network host
        r4 = self.addHost('r4', ip='10.104.0.1/24')
        h4 = self.addHost('h4', ip="10.104.0.251/24")
        s4 = self.addSwitch('s4')

        # r5 network host
        r5 = self.addHost('r5', ip='10.105.0.1/24')
        h5 = self.addHost('h5', ip="10.105.0.251/24")
        s5 = self.addSwitch('s5')

        # Add links based on the above diagram
        # r1 network links
        self.addLink(s1, r1, intfName2='r1-eth0', params2={'ip': '10.1.0.1/24'})
        self.addLink(h1, s1)

        # r2 network links
        self.addLink(s2, r2, intfName2='r2-eth0',
                     params2={'ip': '10.101.0.1/24'})
        self.addLink(h2, s2)

        # r3 network links
        self.addLink(s3, r3, intfName2='r3-eth0',
                     params2={'ip': '10.103.0.1/24'})
        self.addLink(h3, s3)

        # r4 network links
        self.addLink(s4, r4, intfName2='r4-eth0',
                     params2={'ip': '10.104.0.1/24'})
        self.addLink(h4, s4)

        # r5 network links
        self.addLink(s5, r5, intfName2='r5-eth0',
                     params2={'ip': '10.105.0.1/24'})
        self.addLink(h5, s5)

        # links between routers
        self.addLink(r1, r2, intfName1='r1-eth1', intftName2='r2-eth1',
                     params1={'ip': '10.107.0.1/24'},
                     params2={'ip': '10.107.0.2/24'})
        self.addLink(r2, r3, intfName1='r2-eth2', intftName2='r3-eth1',
                     params1={'ip': '10.108.0.1/24'},
                     params2={'ip': '10.108.0.2/24'})
        self.addLink(r3, r4, intfName1='r3-eth2', intftName2='r4-eth1',
                     params1={'ip': '10.109.0.1/24'},
                     params2={'ip': '10.109.0.2/24'})
        self.addLink(r4, r5, intfName1='r4-eth2', intftName2='r5-eth1',
                     params1={'ip': '10.110.0.1/24'},
                     params2={'ip': '10.110.0.2/24'})


topos = {'straight': (lambda: StraightRouter())}

