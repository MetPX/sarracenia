import pytest
from tests.conftest import *

import sarracenia.config
import sarracenia.flow
import copy

__COMPONENT="subscribe"
__CONFIG="flow_class_test"

def __make_fake_config(lines=[]):
    """ build and return a fake config object
    """
    options = copy.deepcopy(sarracenia.config.default_config())
    options.component = __COMPONENT
    options.config = __CONFIG
    options.action = 'start'
    for line in lines:
        options.parse_line(__COMPONENT, __CONFIG, f"{__COMPONENT}/{__CONFIG}", 1, line)
    options.metricsFilename = '/tmp/fake_filename_nothing_here'
    options.novipFilename = options.metricsFilename
    options.acceptUnmatched = False
    options.finalize()
    return options


def test_msg_accepted_with_sundew_extension():
    """
    Regression test for https://github.com/MetPX/sarracenia/issues/1573
    sundew_extension should be included in filtering, even when URL has a port
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # based on the accept statement, the message should only be accepted when the sundew_extension is correctly added
    flow.filter()
    assert(len(flow.worklist.rejected) == 0)
    assert(msg not in flow.worklist.rejected)
    assert(msg in flow.worklist.incoming)

def test_msg_rejected_when_sundew_extension_already_present():
    """
    If the path itself already contains a different sundew extension,
    the sundew_extension header in the msg should not be used for filtering
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt:something:CWAO:SA:3:Direct'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # msg already has a different sundew extension that does not match the accept, it should be rejected
    flow.filter()

    # worklist.rejected gets acked and set to [] at the end of filter
    assert(len(flow.worklist.incoming) == 0)
    assert(len(flow.worklist.rejected) == 0)
    assert(msg not in flow.worklist.incoming)


def __traversal_flow(lines):
    options = __make_fake_config(lines=lines)
    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    return flow


def __inline_message(relPath, **extra):
    message = sarracenia.Message()
    message["pubTime"] = "20261008T120000.123"
    message["baseUrl"] = "none://"
    message["relPath"] = relPath
    message["size"] = 8
    message["content"] = {"encoding": "utf-8", "value": "payload\n"}
    message["identity"] = {"method": "arbitrary", "value": relPath}
    message.update(extra)
    return message


def test_filter_rejects_relpath_escaping_directory_when_mirroring(tmp_path):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror True", f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("../../escape/evil.txt"))
    flow.worklist.incoming.append(__inline_message("a/../../../escape2/evil.txt"))
    flow.worklist.incoming.append(__inline_message("a/b/ok.txt"))

    flow.filter()
    flow.work()

    assert [m["new_file"] for m in flow.worklist.ok] == ["ok.txt"]
    assert (root / "a" / "b" / "ok.txt").read_text() == "payload\n"
    assert not (tmp_path / "escape").exists()
    assert not (tmp_path / "escape2").exists()


def test_filter_rejects_rename_escaping_directory(tmp_path):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror True", f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("sub/a.txt", rename="../../escape3/renamed.txt"))

    flow.filter()
    flow.work()

    assert flow.worklist.ok == []
    assert not (tmp_path / "escape3").exists()


def test_filter_ignores_dotdot_in_directory_part_without_mirror(tmp_path):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror False", f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("../../escape/evil.txt"))

    flow.filter()
    flow.work()

    assert (root / "evil.txt").read_text() == "payload\n"
    assert not (tmp_path / "escape").exists()


def test_filter_accepts_escaping_relpath_with_acceptPathTraversal(tmp_path):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror True", "acceptPathTraversal True",
                                       f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("../../escape/evil.txt"))

    flow.filter()
    flow.work()

    assert (tmp_path / "escape" / "evil.txt").read_text() == "payload\n"


def test_filter_rejects_filename_dotdot_without_mirror(tmp_path, caplog):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror False", f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("a/.."))

    flow.filter()

    assert flow.worklist.incoming == []
    assert len([r for r in caplog.records if r.getMessage().startswith("rejecting a/..:")]) == 1


def test_filter_rejects_dotdot_substituted_into_directory(tmp_path):
    # ${0} is the whole matched url, so the message's relPath ends up in the directory even without mirror
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror False", f"directory {root}/${{0}}",
                                       "accept none://(.*)/[^/]+$"])
    flow.worklist.incoming.append(__inline_message("../../../x/evil.txt"))
    flow.worklist.incoming.append(__inline_message("a/b/ok.txt"))

    flow.filter()
    flow.work()

    assert [m["new_file"] for m in flow.worklist.ok] == ["ok.txt"]
    assert not (tmp_path / "x").exists()


def test_filter_allows_dotdot_from_the_configured_directory(tmp_path):
    # a '..' written by the operator in the directory option is not the message's doing
    root = tmp_path / "data" / "elsewhere" / ".." / "root"
    (tmp_path / "data" / "root").mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror True", f"directory {root}", "accept .*"])
    flow.worklist.incoming.append(__inline_message("a/ok.txt"))
    flow.worklist.incoming.append(__inline_message("../escape/evil.txt"))

    flow.filter()
    flow.work()

    assert [m["new_file"] for m in flow.worklist.ok] == ["ok.txt"]
    assert (tmp_path / "data" / "root" / "a" / "ok.txt").read_text() == "payload\n"
    assert not (tmp_path / "data" / "escape").exists()


@pytest.mark.parametrize("lines", [
    ["post_baseDir {tmp}/data/elsewhere/../root"],
    ["baseDir {tmp}/data/elsewhere/..", "directory ${{BD}}/root"],
    ["baseDir {tmp}/data/elsewhere/..", "post_baseDir ${{BD}}/root", "directory ${{PBD}}"],
])
def test_filter_allows_dotdot_from_the_configured_base_directory(tmp_path, lines):
    # the base directory can come from post_baseDir, ${BD} or ${PBD}, nested or not: all configuration
    (tmp_path / "data" / "root").mkdir(parents=True)
    lines = ["download True", "mirror True"] + [l.format(tmp=tmp_path) for l in lines] + ["accept .*"]
    flow = __traversal_flow(lines)
    flow.worklist.incoming.append(__inline_message("a/ok.txt"))
    flow.worklist.incoming.append(__inline_message("../escape/evil.txt"))

    flow.filter()

    assert [m["new_file"] for m in flow.worklist.incoming] == ["ok.txt"]
    assert flow.worklist.incoming[0]["new_dir"].endswith("/elsewhere/../root/a")


def test_filter_rejects_absolute_filename_from_message(tmp_path, caplog):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    victim = tmp_path / "victim.txt"
    flow = __traversal_flow(["download True", "mirror False", f"directory {root}",
                                       "filename SENDER", "accept .*"])
    flow.worklist.incoming.append(__inline_message("sub/plain.txt", sundew_extension=f"SENDER={victim}"))

    flow.filter()
    flow.work()

    assert flow.worklist.ok == []
    assert not victim.exists()
    assert len([r for r in caplog.records if "is absolute" in r.getMessage()]) == 1


def test_filter_skips_the_check_when_not_downloading(tmp_path):
    # a shovel or post relays the path as is, the subscriber at the other end does its own check
    flow = __traversal_flow(["download False", "mirror True", "accept .*"])
    flow.worklist.incoming.append(__inline_message("a/../b/ok.txt"))

    flow.filter()

    assert [m["new_file"] for m in flow.worklist.incoming] == ["ok.txt"]


def test_filter_rejects_when_no_file_name_can_be_derived(tmp_path, caplog):
    root = tmp_path / "data" / "root"
    root.mkdir(parents=True)
    flow = __traversal_flow(["download True", "mirror False", f"directory {root}", "filename SENDER", "accept .*"])
    flow.worklist.incoming.append(__inline_message("sub/plain.txt"))

    flow.filter()

    assert flow.worklist.incoming == []
    assert len([r for r in caplog.records if "could not derive a file name" in r.getMessage()]) == 1
