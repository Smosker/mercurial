  $ . $TESTDIR/wireprotohelpers.sh

  $ hg init server
  $ enablehttpv2 server
  $ cd server
  $ hg debugdrawdag << EOF
  > C D
  > |/
  > B
  > |
  > A
  > EOF

  $ hg log -T '{rev}:{node} {desc}\n'
  3:be0ef73c17ade3fc89dc41701eb9fc3a91b58282 D
  2:26805aba1e600a82e93661149f2313866a221a7b C
  1:112478962961147124edd43549aedd1a335e44bf B
  0:426bada5c67598ca65036d57d9e4b64b0c1ce7a0 A

  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ cat hg.pid > $DAEMON_PIDS

No arguments returns something reasonable

  $ sendhttpv2peer << EOF
  > command known
  > EOF
  creating http peer for wire protocol version 2
  sending known command
  s>     POST /api/exp-http-v2-0001/ro/known HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 20\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     \x0c\x00\x00\x01\x00\x01\x01\x11\xa1DnameEknown
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     14\r\n
  s>     \x0c\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBok@
  s>     \r\n
  received frame(size=12; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: []

Single known node works

  $ sendhttpv2peer << EOF
  > command known
  >     nodes eval:[b'\x42\x6b\xad\xa5\xc6\x75\x98\xca\x65\x03\x6d\x57\xd9\xe4\xb6\x4b\x0c\x1c\xe7\xa0']
  > EOF
  creating http peer for wire protocol version 2
  sending known command
  s>     POST /api/exp-http-v2-0001/ro/known HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 54\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     .\x00\x00\x01\x00\x01\x01\x11\xa2Dargs\xa1Enodes\x81TBk\xad\xa5\xc6u\x98\xcae\x03mW\xd9\xe4\xb6K\x0c\x1c\xe7\xa0DnameEknown
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     15\r\n
  s>     \r\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBokA1
  s>     \r\n
  received frame(size=13; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: [True]

Multiple nodes works

  $ sendhttpv2peer << EOF
  > command known
  >     nodes eval:[b'\x42\x6b\xad\xa5\xc6\x75\x98\xca\x65\x03\x6d\x57\xd9\xe4\xb6\x4b\x0c\x1c\xe7\xa0', b'00000000000000000000', b'\x11\x24\x78\x96\x29\x61\x14\x71\x24\xed\xd4\x35\x49\xae\xdd\x1a\x33\x5e\x44\xbf']
  > EOF
  creating http peer for wire protocol version 2
  sending known command
  s>     POST /api/exp-http-v2-0001/ro/known HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 96\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     X\x00\x00\x01\x00\x01\x01\x11\xa2Dargs\xa1Enodes\x83TBk\xad\xa5\xc6u\x98\xcae\x03mW\xd9\xe4\xb6K\x0c\x1c\xe7\xa0T00000000000000000000T\x11$x\x96)a\x14q$\xed\xd45I\xae\xdd\x1a3^D\xbfDnameEknown
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     17\r\n
  s>     \x0f\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBokC101
  s>     \r\n
  received frame(size=15; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: [True, False, True]

  $ cat error.log
