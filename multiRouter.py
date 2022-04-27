import os

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo


class MultiRouter(Topo):
    """
        A multi-router network topology to test basic functionality of router broadcasting and advertising

                                        s5 ----- h7
                                      /
                                    /
                                   r3
                              /        \
                            /            \
                           r1 ----------- r2
                          |  \          |  \
                         |    \        |    \
                        s1    s2       s3    s4
                      /   \   /  \     |      \
                     h1   h2 h3  h4   h5      h6
        The ip address of hosts and interfaces in this topology is static.
    """

    def __init__(self, **params):
        Topo.__init__(self)

        # Add hosts and switches
        # r1 network hosts
        r1 = self.addHost('r1', ip='10.1.0.1/24',
                          hostRoute='10.101.0.1 via 10.104.0.1')
        h1 = self.addHost('h1', ip='10.1.0.251/24')
        h2 = self.addHost('h2', ip='10.1.0.252/24')
        h3 = self.addHost('h3', ip="10.100.0.251/24",
                          defaultRoute='via 10.100.0.1')
        h4 = self.addHost('h4', ip="10.100.0.252/24",
                          defaultRoute='via 10.100.0.1')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # r2 network hosts
        r2 = self.addHost('r2', ip='10.101.0.1/24')
        h5 = self.addHost('h5', ip='10.101.0.251/24')
        h6 = self.addHost('h6', ip='10.102.0.251/24')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')

        # r3 network host
        r3 = self.addHost('r3', ip='10.103.0.1/24')
        h7 = self.addHost('h7', ip='10.103.0.251/24')
        s5 = self.addSwitch('s5')

        # switches between routers
        s6 = self.addSwitch('s6')

        # Add links based on the above diagram
        # r1 network links
        self.addLink(s1, r1, intfName2='r1-eth0', params2={'ip': '10.1.0.1/24'})
        self.addLink(s2, r1, intfName2='r1-eth1',
                     params2={'ip': '10.100.0.1/24'})

        self.addLink(h1, s1)
        self.addLink(h2, s1)

        self.addLink(h3, s2)
        self.addLink(h4, s2)

        # r2 network links
        self.addLink(s3, r2, intfName2='r2-eth0',
                     params2={'ip': '10.101.0.1/24'})
        self.addLink(s4, r2, intfName2='r2-eth1',
                     params2={'ip': '10.102.0.1/24'})
        self.addLink(h5, s3)
        self.addLink(h6, s4)

        # r3 network links
        self.addLink(s5, r3, intfName2='r3-eth0',
                     params2={'ip': '10.103.0.1/24'})
        self.addLink(h7, s5)

        # links between routers
        self.addLink(r1, r2, intfName1='r1-eth2', intftName2='r2-eth2',
                     params1={'ip': '10.104.0.1/24'},
                     params2={'ip': '10.104.0.2/24'})
        self.addLink(r1, r3, intfName1='r1-eth3', intftName2='r3-eth1',
                     params1={'ip': '10.105.0.1/24'},
                     params2={'ip': '10.105.0.2/24'})
        self.addLink(r2, r3, intfName1='r2-eth3', intftName2='r3-eth2',
                     params1={'ip': '10.106.0.1/24'},
                     params2={'ip': '10.106.0.2/24'})


topos = {'multiRouter': (lambda: MultiRouter())}
