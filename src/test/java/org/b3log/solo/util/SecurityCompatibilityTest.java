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
package org.b3log.solo.util;

import com.rometools.rome.io.SyndFeedInput;
import java.io.StringReader;
import java.util.List;
import java.util.Map;
import org.eclipse.jetty.ee8.webapp.WebDescriptor;
import org.jsoup.Jsoup;
import org.jsoup.safety.Safelist;
import org.testng.annotations.Test;
import org.xml.sax.InputSource;
import org.yaml.snakeyaml.error.YAMLException;

import static org.testng.Assert.*;

public class SecurityCompatibilityTest {
    @Test
    public void legacyFrameworkStringAndArrayCallsRemainBinaryCompatible() throws Exception {
        final Class<?> strings = Class.forName("org.apache.commons.lang.StringUtils");
        assertEquals(strings.getMethod("isBlank", String.class).invoke(null, (Object) null), true);
        assertEquals(strings.getMethod("contains", String.class, String.class).invoke(null, "abc", "b"), true);
        assertEquals(strings.getMethod("countMatches", String.class, String.class).invoke(null, "ab-ab", "ab"), 2);
        assertEquals(strings.getMethod("substringBetween", String.class, String.class, String.class)
                .invoke(null, "prefix[value]suffix", "[", "]"), "value");
        assertEquals(strings.getMethod("startsWithAny", String.class, String[].class)
                .invoke(null, "prefix-value", new String[] {"other", "prefix"}), true);
        assertEquals(org.apache.commons.lang.ArrayUtils.getLength(new int[] {1, 2}), 2);
        assertEquals(org.apache.commons.lang.ArrayUtils.getLength(null), 0);
        final long timestamp = java.time.Instant.parse("2020-07-01T12:00:00Z").toEpochMilli();
        assertEquals(org.apache.commons.lang.time.DateFormatUtils.format(timestamp, "yyyy"), "2020");
    }

    @Test
    public void retiredVulnerableLibrariesAreNotOnTheRuntimeClasspath() {
        assertThrows(ClassNotFoundException.class, () -> Class.forName("org.apache.commons.lang.ClassUtils"));
        assertThrows(ClassNotFoundException.class, () -> Class.forName("org.jdom.Document"));
        assertThrows(ClassNotFoundException.class, () -> Class.forName("com.sun.syndication.io.SyndFeedInput"));
        assertTrue(org.apache.log4j.Logger.class.getProtectionDomain().getCodeSource()
                .getLocation().toString().contains("reload4j"));
    }

    @Test
    public void servletDescriptorParserCanLoadItsXmlCatalogs() throws Exception {
        final String descriptor = "<web-app xmlns='http://xmlns.jcp.org/xml/ns/javaee' version='3.1'/>";
        final var root = WebDescriptor.newParser(false).parse(new InputSource(new StringReader(descriptor)));
        assertEquals(root.getTag(), "web-app");
    }

    @Test
    public void normalArticleFrontMatterCanStillBeImported() {
        final Map<?, ?> front = SafeYaml.createLoader().load("title: Security update\ntags: [java, blog]\n");
        assertEquals(front.get("title"), "Security update");
        assertEquals(front.get("tags"), List.of("java", "blog"));
    }

    @Test
    public void articleFrontMatterRejectsJavaObjectConstruction() {
        assertThrows(YAMLException.class,
                () -> SafeYaml.createLoader().load("!!javax.script.ScriptEngineManager []"));
    }

    @Test
    public void articleFrontMatterLimitsAliasExpansion() {
        final String yaml = "base: &base [one, two]\nitems: [" + "*base,".repeat(51) + "*base]\n";
        assertThrows(YAMLException.class, () -> SafeYaml.createLoader().load(yaml));
    }

    @Test
    public void feedImportRejectsDocumentTypesAndEntities() {
        final SyndFeedInput parser = new SyndFeedInput();
        parser.setAllowDoctypes(false);
        final String xml = "<!DOCTYPE rss [<!ENTITY external SYSTEM 'file:///definitely-not-a-real-file'>]>"
                + "<rss version='2.0'><channel><title>&external;</title><link>https://example.com</link>"
                + "<description>test</description></channel></rss>";
        assertThrows(Exception.class, () -> parser.build(new StringReader(xml)));
    }

    @Test
    public void commentSanitizerRemovesExecutableLinks() {
        final String html = Jsoup.clean("<a href='javascript:alert(1)'>click</a><img src=x onerror='alert(1)'>",
                "https://example.com/", Safelist.basic().preserveRelativeLinks(true));
        assertFalse(html.contains("javascript:"));
        assertFalse(html.contains("onerror"));
    }

    @Test
    public void cosUploadClientDoesNotRequireOptionalKmsCredentialsProviders() {
        final com.qcloud.cos.COSClient client = new com.qcloud.cos.COSClient(
                new com.qcloud.cos.auth.BasicCOSCredentials("test-id", "test-key"),
                new com.qcloud.cos.ClientConfig(new com.qcloud.cos.region.Region("ap-beijing")));
        client.shutdown();
    }
}
