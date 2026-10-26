/*
 * Bolo - A stable and beautiful blogging system based in Solo.
 * Copyright (c) 2020-present, https://github.com/bolo-blog
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
/**
 *  about for admin
 *
 * @author <a href="http://vanessa.b3log.org">Liyuan Li</a>
 * @author <a href="http://88250.b3log.org">Liang Ding (Solo Author)</a>
 * @author <a href="https://github.com/adlered">adlered (Bolo Author)</a>
 * @author <a href="https://github.com/gakkiyomi">gakkiyomi (Bolo Commiter)</a>
 */

/* about 相关操作 */
admin.about = {
  init: function () {
    const current = parseVersion(version.split(' ')[0]);
    const releasesURL = 'https://github.com/bolo-blog/bolo-solo/releases';

    if (version.split(' ')[1] === '内测版') {
      $('#updateCheck').html('🍍 <font style="color: #3caf36">您正在使用菠萝博客内测版本，感谢您对开源的贡献！</font>');
      return;
    }

    function parseVersion (value) {
      const match = /^v?(\d+(?:\.\d+)*)(?:[-_]stable)?$/.exec(value);
      return match ? match[1].split('.').map(Number) : null;
    }

    function compareVersions (a, b) {
      for (let i = 0; i < Math.max(a.length, b.length); i++) {
        const difference = (a[i] || 0) - (b[i] || 0);
        if (difference !== 0) return difference;
      }
      return 0;
    }

    function checkFailed () {
      $('#updateCheck').html('<a href="' + releasesURL + '" target="_blank" rel="noopener noreferrer">版本更新检查失败，点击手动查看版本公告。</a>');
    }

    $.ajax({
      url: 'https://api.github.com/repos/bolo-blog/bolo-solo/releases/latest',
      dataType: 'json',
      timeout: 10000,
      success: function (release) {
        const latest = parseVersion(release.tag_name || '');
        if (!current || !latest || release.draft || release.prerelease) {
          checkFailed();
          return;
        }
        if (compareVersions(current, latest) >= 0) {
          $('#updateCheck').html('🍍 <font style="color: #3caf36">你正在使用菠萝博客最新版！</font>');
        } else {
          $('<a>', {
            href: releasesURL,
            target: '_blank',
            rel: 'noopener noreferrer',
            text: '菠萝博客 ' + release.tag_name + ' 已推出，赶快更新吧！',
          }).css('color', '#991a1a').appendTo($('#updateCheck').empty());
        }
        $('#tipMsg').text('');
        $('#loadMsg').text('');
      },
      error: checkFailed,
    });
  }
}


/*
 * 注册到 admin 进行管理 
 */
admin.register['about'] = {
  'obj': admin.about,
  'init': admin.about.init,
  'refresh': function () {
    admin.clearTip()
  }
};