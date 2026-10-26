<#--

    Bolo - A stable and beautiful blogging system based in Solo.
    Copyright (c) 2020-present, https://github.com/bolo-blog

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

-->
<div class="module-panel">
    <div class="module-header">
        <h2>${aboutLabel}</h2>
    </div>
    <div class="module-body padding12 fn__flex">
        <div class="about-logo">
            <a href="https://github.com/adlered/bolo-solo" target="_blank">
                <img width="128" src="${staticServePath}/images/logo.png" alt="Bolo 重塑经典，致敬 Solo" title="Bolo 重塑经典，致敬 Solo" />
            </a>
        </div>
        <div class="about__panel">
            <div class="about-margin fn__left">
                您正在使用 菠萝博客 Bolo<br>
                当前 Bolo 版本：${boloVersion}<br>
            </div>

            <a href="https://github.com/bolo-blog/bolo-solo" target="_blank" rel="noopener noreferrer"
               class="fn__left" style="margin: 21px 0 0 20px">在 GitHub 上支持菠萝博客</a>
            <div class="fn__clear"></div>
            <script type="text/javascript">
                var version = '${boloVersion}';
            </script>
            <b><p id="updateCheck">正在检查版本更新...</p></b>
        </div>
    </div>
    <span class="fn__clear">
        <div style="margin: 25px 25px 0px 25px">
            <a href="https://github.com/bolo-blog/bolo-solo#readme" target="_blank" rel="noopener noreferrer">查看项目文档</a>
        </div>
    </span>
    <br><br>
</div>

${plugins}
