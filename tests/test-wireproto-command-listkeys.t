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

  $ hg phase --public -r C
  $ hg book -r C @

  $ hg log -T '{rev}:{node} {desc}\n'
  3:be0ef73c17ade3fc89dc41701eb9fc3a91b58282 D
  2:26805aba1e600a82e93661149f2313866a221a7b C
  1:112478962961147124edd43549aedd1a335e44bf B
  0:426bada5c67598ca65036d57d9e4b64b0c1ce7a0 A

  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ cat hg.pid > $DAEMON_PIDS

Request for namespaces works

  $ sendhttpv2peer << EOF
  > command listkeys
  >     namespace namespaces
  > EOF
  creating http peer for wire protocol version 2
  sending listkeys command
  s>     POST /api/exp-http-v2-0001/ro/listkeys HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 50\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     *\x00\x00\x01\x00\x01\x01\x11\xa2Dargs\xa1InamespaceJnamespacesDnameHlistkeys
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     33\r\n
  s>     +\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBok\xa3Fphases@Ibookmarks@Jnamespaces@
  s>     \r\n
  received frame(size=43; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: {b'bookmarks': b'', b'namespaces': b'', b'phases': b''}

Request for phases works

  $ sendhttpv2peer << EOF
  > command listkeys
  >     namespace phases
  > EOF
  creating http peer for wire protocol version 2
  sending listkeys command
  s>     POST /api/exp-http-v2-0001/ro/listkeys HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 46\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     &\x00\x00\x01\x00\x01\x01\x11\xa2Dargs\xa1InamespaceFphasesDnameHlistkeys
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     50\r\n
  s>     H\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBok\xa2JpublishingDTrueX(be0ef73c17ade3fc89dc41701eb9fc3a91b58282A1
  s>     \r\n
  received frame(size=72; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: {b'be0ef73c17ade3fc89dc41701eb9fc3a91b58282': b'1', b'publishing': b'True'}

Request for bookmarks works

  $ sendhttpv2peer << EOF
  > command listkeys
  >     namespace bookmarks
  > EOF
  creating http peer for wire protocol version 2
  sending listkeys command
  s>     POST /api/exp-http-v2-0001/ro/listkeys HTTP/1.1\r\n
  s>     Accept-Encoding: identity\r\n
  s>     accept: application/mercurial-exp-framing-0005\r\n
  s>     content-type: application/mercurial-exp-framing-0005\r\n
  s>     content-length: 49\r\n
  s>     host: $LOCALIP:$HGPORT\r\n (glob)
  s>     user-agent: Mercurial debugwireproto\r\n
  s>     \r\n
  s>     )\x00\x00\x01\x00\x01\x01\x11\xa2Dargs\xa1InamespaceIbookmarksDnameHlistkeys
  s> makefile('rb', None)
  s>     HTTP/1.1 200 OK\r\n
  s>     Server: testing stub value\r\n
  s>     Date: $HTTP_DATE$\r\n
  s>     Content-Type: application/mercurial-exp-framing-0005\r\n
  s>     Transfer-Encoding: chunked\r\n
  s>     \r\n
  s>     40\r\n
  s>     8\x00\x00\x01\x00\x02\x012
  s>     \xa1FstatusBok\xa1A@X(26805aba1e600a82e93661149f2313866a221a7b
  s>     \r\n
  received frame(size=56; request=1; stream=2; streamflags=stream-begin; type=command-response; flags=eos)
  s>     0\r\n
  s>     \r\n
  response: {b'@': b'26805aba1e600a82e93661149f2313866a221a7b'}

  $ cat error.log
