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
package org.apache.commons.lang;

/**
 * Binary compatibility for Latke 2.5.8. Implementations delegate to supported Lang 3.
 * The obsolete Commons Lang 2 library, including ClassUtils, is not packaged.
 */
public final class StringUtils {
    private StringUtils() { }
    public static boolean contains(String value, String search) { return org.apache.commons.lang3.StringUtils.contains(value, search); }
    public static int countMatches(String value, String search) { return org.apache.commons.lang3.StringUtils.countMatches(value, search); }
    public static boolean equals(String first, String second) { return org.apache.commons.lang3.StringUtils.equals(first, second); }
    public static boolean equalsIgnoreCase(String first, String second) { return org.apache.commons.lang3.StringUtils.equalsIgnoreCase(first, second); }
    public static boolean isBlank(String value) { return org.apache.commons.lang3.StringUtils.isBlank(value); }
    public static boolean isNotBlank(String value) { return org.apache.commons.lang3.StringUtils.isNotBlank(value); }
    public static String replace(String text, String search, String replacement) { return org.apache.commons.lang3.StringUtils.replace(text, search, replacement); }
    public static boolean startsWithAny(String value, String... prefixes) { return org.apache.commons.lang3.StringUtils.startsWithAny(value, prefixes); }
    public static boolean startsWithIgnoreCase(String value, String prefix) { return org.apache.commons.lang3.StringUtils.startsWithIgnoreCase(value, prefix); }
    public static String substringAfter(String value, String separator) { return org.apache.commons.lang3.StringUtils.substringAfter(value, separator); }
    public static String substringBefore(String value, String separator) { return org.apache.commons.lang3.StringUtils.substringBefore(value, separator); }
    public static String substringBetween(String value, String open, String close) { return org.apache.commons.lang3.StringUtils.substringBetween(value, open, close); }
    public static String[] substringsBetween(String value, String open, String close) { return org.apache.commons.lang3.StringUtils.substringsBetween(value, open, close); }
    public static String trim(String value) { return org.apache.commons.lang3.StringUtils.trim(value); }
}
