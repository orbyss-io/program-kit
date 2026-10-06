using System.Globalization;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Npgsql;

namespace Notes.Oracle;

internal static class NotesBehaviorOracle
{
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);
    private static int assertions;

    internal static async Task RunAsync(string host, string issuer)
    {
        if (Environment.GetEnvironmentVariable("NOTES_ORACLE_DISPOSABLE") != "true")
            throw new InvalidOperationException("The oracle requires an explicitly disposable database.");
        var connectionString = Environment.GetEnvironmentVariable("NOTES_ORACLE_CONNECTION")
            ?? throw new InvalidOperationException("A disposable PostgreSQL connection is required.");
        await using var database = new NpgsqlConnection(connectionString);
        await database.OpenAsync();
        Require(await ScalarAsync<long>(database, "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") == 0,
            "The oracle refuses a nonempty database.");
        await SqlAsync(database, await File.ReadAllTextAsync(Path.Combine(AppContext.BaseDirectory, "schema.sql")));
        using var anonymous = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false }) { BaseAddress = new(host) };
        await ProblemAsync(anonymous, HttpMethod.Get, "/api/notes", 401);
        await ProblemAsync(anonymous, HttpMethod.Get, "/bff/access-denied", 403);
        using var alice = await LoginAsync(host, issuer, "alice");
        using var bob = await LoginAsync(host, issuer, "bob");
        var note = Id(1);
        var create = new { operationId = Id(101), noteId = note, name = "First Ω 💡" };
        var original = await SuccessAsync(alice, "/api/notes", create);
        Require(original.GetProperty("operationId").GetGuid() == Id(101)
            && original.GetProperty("note").GetProperty("revision").GetInt64() == 1, "Create acknowledgement identity/revision changed.");
        var parallelReads = await Task.WhenAll(Enumerable.Range(0, 16).Select(_ => GetAsync(alice, "/api/notes/" + note)));
        Require(parallelReads.All(read => read.GetProperty("note").GetProperty("revision").GetInt64() == 1),
            "Independent concurrent reads did not retain the admitted note.");
        Require((await SuccessAsync(alice, "/api/notes", create)).GetRawText() == original.GetRawText(), "Identical create replay changed acknowledgement.");
        using (var rawReplay = new HttpRequestMessage(HttpMethod.Post, "/api/notes"))
        {
            rawReplay.Content = new StringContent(" { \n\"operationId\" : \"" + Id(101).ToString().ToUpperInvariant()
                + "\", \"noteId\" : \"" + note.ToString().ToUpperInvariant() + "\", \"name\" : "
                + JsonSerializer.Serialize(create.name) + " } ", System.Text.Encoding.UTF8, "application/json");
            rawReplay.Headers.Add("X-CSRF-TOKEN", alice.Antiforgery);
            using var response = await alice.Client.SendAsync(rawReplay);
            Require(response.StatusCode == HttpStatusCode.OK && (await JsonAsync(response)).GetRawText() == original.GetRawText(),
                "JSON whitespace/GUID spelling changed the admitted exact packet identity.");
        }
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes", 409, new { operationId = Id(101), noteId = note, name = create.name + " " });
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes", 409, new { operationId = Id(101), noteId = note, name = "changed packet" });
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes", 409, new { operationId = Id(101), noteId = Id(2), name = create.name });
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes/" + note + "/rename", 409,
            new { operationId = Id(101), expectedRevision = 1, name = create.name });
        await ProblemAsync(bob, HttpMethod.Get, "/api/notes/" + note, 404);
        await ProblemAsync(bob, HttpMethod.Post, "/api/notes/" + note + "/rename", 404,
            new { operationId = Id(201), expectedRevision = 1, name = "foreign owner" });
        Require((await GetAsync(bob, "/api/notes?size=2")).GetProperty("items").GetArrayLength() == 0,
            "An ownership cursor/query disclosed another owner's note.");
        // Same note and operation IDs are legitimate for a distinct authenticated owner.
        await SuccessAsync(bob, "/api/notes", new { operationId = Id(101), noteId = note, name = "Bob" });
        var rename = new { operationId = Id(102), expectedRevision = 1, name = "Second" };
        var renamed = await SuccessAsync(alice, "/api/notes/" + note + "/rename", rename);
        Require(renamed.GetProperty("note").GetProperty("revision").GetInt64() == 2, "Rename did not increment revision.");
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes/" + note + "/rename", 409,
            new { operationId = Id(102), expectedRevision = 2, name = rename.name });
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes/" + note + "/rename", 409,
            new { operationId = Id(102), expectedRevision = 1, name = "changed rename packet" });
        Require((await SuccessAsync(alice, "/api/notes", create)).GetRawText() == original.GetRawText(),
            "Replay followed the mutable head instead of the immutable receipt.");
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes/" + note + "/rename", 409,
            new { operationId = Id(103), expectedRevision = 1, name = "stale" });
        var race = await Task.WhenAll(PostAsync(alice, "/api/notes/" + note + "/rename",
            new { operationId = Id(104), expectedRevision = 2, name = "Winner A" }),
            PostAsync(alice, "/api/notes/" + note + "/rename", new { operationId = Id(105), expectedRevision = 2, name = "Winner B" }));
        try
        {
            Require(race.Count(response => response.StatusCode == HttpStatusCode.OK) == 1
                && race.Count(response => response.StatusCode == HttpStatusCode.Conflict) == 1,
                "Concurrent expected-revision mutation did not have exactly one winner.");
            foreach (var failure in race.Where(response => response.StatusCode == HttpStatusCode.Conflict)) await AdmitProblemAsync(failure, 409);
        }
        finally { foreach (var response in race) response.Dispose(); }
        // A delayed acknowledgement/transport loss is not evidence of rollback.
        var uncertain = new { operationId = Id(106), expectedRevision = 3, name = "Committed but response lost" };
        using (var lost = new HttpRequestMessage(HttpMethod.Post, issuer + "/drop-response/api/notes/" + note + "/rename"))
        {
            lost.Content = JsonContent.Create(uncertain, options: Json);
            lost.Headers.Add("Cookie", alice.Cookies.GetCookieHeader(new Uri(host)));
            lost.Headers.Add("X-CSRF-TOKEN", alice.Antiforgery);
            try { using var response = await alice.Client.SendAsync(lost); throw new InvalidOperationException("The lost-response proxy returned an acknowledgement."); }
            catch (HttpRequestException) { }
        }
        var reconciled = await SuccessAsync(alice, "/api/notes/" + note + "/rename", uncertain);
        Require(reconciled.GetProperty("note").GetProperty("revision").GetInt64() == 4,
            "Exact retry after uncertain transport did not reconcile the committed receipt.");
        Require(await CountAsync(database, "note_revisions", issuer, "alice", note) == 4, "Retry duplicated a business revision.");
        Require((await SuccessAsync(alice, "/api/notes/" + note + "/rename", rename)).GetRawText() == renamed.GetRawText(),
            "Rename replay followed the newer head instead of its original acknowledgement.");
        await RejectCorruptHeadAsync(database, issuer, note, revision: 99, name: "Committed but response lost");
        await RejectCorruptHeadAsync(database, issuer, note, revision: 4, name: "Mismatched stored head");
        await using (var corruptReceipt = new NpgsqlCommand("UPDATE note_receipts SET name='Mismatched frozen acknowledgement' WHERE issuer=$1 AND subject='alice' AND operation_id=$2", database))
        {
            corruptReceipt.Parameters.AddWithValue(issuer); corruptReceipt.Parameters.AddWithValue(Id(101));
            try { await corruptReceipt.ExecuteNonQueryAsync(); throw new OracleAssertionException("Native schema admitted a mismatched receipt snapshot."); }
            catch (PostgresException failure) when (failure.SqlState == "23503" && failure.ConstraintName == "fk_receipt_revision") { }
        }
        // Inject failure after the head/history changes but before the receipt insert completes.
        await SqlAsync(database, "CREATE FUNCTION fixture_receipt_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'PRIVATE_SQL_SENTINEL' USING ERRCODE='P0001'; END $$; CREATE TRIGGER fixture_receipt_failure BEFORE INSERT ON note_receipts FOR EACH ROW EXECUTE FUNCTION fixture_receipt_failure();");
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes/" + note + "/rename", 503,
            new { operationId = Id(107), expectedRevision = 4, name = "Must roll back" });
        Require((await GetAsync(alice, "/api/notes/" + note)).GetProperty("note").GetProperty("revision").GetInt64() == 4,
            "Failed receipt insert leaked a changed head.");
        Require(await CountAsync(database, "note_revisions", issuer, "alice", note) == 4, "Failed transaction leaked history.");
        await SqlAsync(database, "DROP TRIGGER fixture_receipt_failure ON note_receipts; DROP FUNCTION fixture_receipt_failure();");
        // A storage invariant defect remains a safe server failure, never broad ArgumentException->400.
        var invalidNote = Id(9000);
        await using (var corrupt = new NpgsqlCommand("WITH invalid AS (INSERT INTO notes(issuer,subject,id,revision,name) VALUES ($1,$2,$3,1,'') RETURNING issuer,subject,id,revision,name) INSERT INTO note_revisions(issuer,subject,id,revision,name) SELECT issuer,subject,id,revision,name FROM invalid", database))
        {
            corrupt.Parameters.AddWithValue(issuer); corrupt.Parameters.AddWithValue("alice"); corrupt.Parameters.AddWithValue(invalidNote);
            await corrupt.ExecuteNonQueryAsync();
        }
        await ProblemAsync(alice, HttpMethod.Get, "/api/notes/" + invalidNote, 500);
        await using (var cleanup = await database.BeginTransactionAsync())
        {
            foreach (var table in new[] { "note_revisions", "notes" })
            {
                await using var remove = new NpgsqlCommand("DELETE FROM " + table + " WHERE issuer=$1 AND subject=$2 AND id=$3", database, cleanup);
                remove.Parameters.AddWithValue(issuer); remove.Parameters.AddWithValue("alice"); remove.Parameters.AddWithValue(invalidNote);
                await remove.ExecuteNonQueryAsync();
            }
            await cleanup.CommitAsync();
        }
        await ProblemAsync(alice, HttpMethod.Post, "/api/notes", 400, new { operationId = Id(108), noteId = Id(2), name = " " });
        await ProblemAsync(alice, HttpMethod.Get, "/api/notes?size=501", 400);
        await ProblemAsync(alice, HttpMethod.Delete, "/api/notes", 405);
        using (var malformed = new HttpRequestMessage(HttpMethod.Post, "/api/notes") { Content = new StringContent("{\"operationId\":null,\"operationId\":null}", System.Text.Encoding.UTF8, "application/json") })
        {
            malformed.Headers.Add("X-CSRF-TOKEN", alice.Antiforgery);
            using var response = await alice.Client.SendAsync(malformed); await AdmitProblemAsync(response, 400);
        }
        using (var oversized = new HttpRequestMessage(HttpMethod.Post, "/api/notes") { Content = new StringContent(new string(' ', 2097153), System.Text.Encoding.UTF8, "application/json") })
        {
            oversized.Headers.Add("X-CSRF-TOKEN", alice.Antiforgery);
            using var response = await alice.Client.SendAsync(oversized); await AdmitProblemAsync(response, 413);
        }
        for (var index = 2; index <= 8; index++)
            await SuccessAsync(alice, "/api/notes", new { operationId = Id(110 + index), noteId = Id(index), name = new string('\uffff', 256) });
        var seen = new HashSet<Guid>();
        string? after = null;
        var pages = 0;
        do
        {
            var page = await GetAsync(alice, "/api/notes?size=2" + (after is null ? "" : "&after=" + after));
            Require(page.GetProperty("items").GetArrayLength() is > 0 and <= 2, "Page violated configured count bound.");
            foreach (var item in page.GetProperty("items").EnumerateArray()) Require(seen.Add(item.GetProperty("id").GetGuid()), "Paging duplicated a note.");
            after = page.GetProperty("nextAfterNoteId").ValueKind == JsonValueKind.Null ? null : page.GetProperty("nextAfterNoteId").GetString();
            pages++;
            Require(pages <= 5, "Paging did not terminate within the declared finite set.");
        } while (after is not null);
        Require(seen.SetEquals(Enumerable.Range(1, 8).Select(Id)), "Paging omitted or mixed another owner's note.");
        // Synthetic data is an oracle input in this disposable database. It admits
        // the largest supported single-item text and then requests the configured
        // maximum count through the actual packaged API/provider/serializer.
        await using (var synthetic = new NpgsqlCommand("WITH inserted AS (INSERT INTO notes(issuer,subject,id,revision,name) SELECT $1,$2,('00000000-0000-0000-0001-'||lpad(to_hex(n),12,'0'))::uuid,1,$3 FROM generate_series(1,500) n RETURNING issuer,subject,id,revision,name) INSERT INTO note_revisions(issuer,subject,id,revision,name) SELECT issuer,subject,id,revision,name FROM inserted", database))
        {
            synthetic.Parameters.AddWithValue(issuer); synthetic.Parameters.AddWithValue("bob"); synthetic.Parameters.AddWithValue(new string('\uffff', 256));
            await synthetic.ExecuteNonQueryAsync();
        }
        using (var maximum = await bob.Client.GetAsync("/api/notes?size=500"))
        {
            var bytes = await maximum.Content.ReadAsByteArrayAsync();
            Require(maximum.StatusCode == HttpStatusCode.OK && bytes.Length is > 750000 and <= 1048576,
                "Largest supported Unicode page was reduced, bypassed its byte contract or exceeded its configured maximum.");
            using var document = JsonDocument.Parse(bytes);
            var page = document.RootElement;
            Require(page.GetProperty("items").GetArrayLength() == 500, "Configured maximum page count was not supported.");
            var last = page.GetProperty("nextAfterNoteId").GetGuid();
            var tail = await GetAsync(bob, "/api/notes?size=500&after=" + last);
            Require(tail.GetProperty("items").GetArrayLength() == 1 && tail.GetProperty("nextAfterNoteId").ValueKind == JsonValueKind.Null,
                "Maximum page did not retain coherent continuation.");
        }
        Require(await ScalarAsync<long>(database, "SELECT count(*) FROM notes n LEFT JOIN note_revisions r USING (issuer,subject,id,revision) WHERE r.id IS NULL OR n.name<>r.name") == 0,
            "Head/revision coherence was not retained.");
        Console.WriteLine($"Notes oracle passed {assertions} independent HTTP/PostgreSQL assertions: ownership, exact replay, revision races, rollback, uncertain transport, paging and common bounded failures.");
    }

    private static async Task<Session> LoginAsync(string host, string issuer, string subject)
    {
        var cookies = new CookieContainer();
        var client = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, CookieContainer = cookies }) { BaseAddress = new(host) };
        using var challenge = await client.GetAsync("/bff/login");
        Require(challenge.StatusCode == HttpStatusCode.Redirect && challenge.Headers.Location!.AbsoluteUri.StartsWith(issuer + "/authorize", StringComparison.Ordinal), "Native OIDC challenge failed.");
        using var authorization = await client.GetAsync(challenge.Headers.Location!.AbsoluteUri + "&fixture_subject=" + subject);
        Require(authorization.StatusCode == HttpStatusCode.Redirect, "Fixture authorization failed.");
        using var callback = await client.GetAsync(authorization.Headers.Location);
        Require(callback.StatusCode == HttpStatusCode.Redirect && callback.Headers.Contains("Set-Cookie"), "Native signed OIDC callback did not issue a cookie.");
        using var user = await client.GetAsync("/bff/user");
        var projected = await JsonAsync(user);
        Require(projected.GetProperty("authenticated").GetBoolean() && projected.GetProperty("issuer").GetString() == issuer
            && projected.GetProperty("subject").GetString() == subject, "Validated identity projection changed.");
        using var antiforgery = await client.GetAsync("/bff/antiforgery");
        var token = (await JsonAsync(antiforgery)).GetProperty("requestToken").GetString()!;
        return new(client, cookies, token);
    }

    private static async Task<JsonElement> SuccessAsync(Session session, string path, object packet)
    {
        using var response = await PostAsync(session, path, packet);
        Require(response.StatusCode == HttpStatusCode.OK, "Expected mutation success: " + (int)response.StatusCode);
        return await JsonAsync(response);
    }
    private static Task<HttpResponseMessage> PostAsync(Session session, string path, object packet)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, path) { Content = JsonContent.Create(packet, options: Json) };
        request.Headers.Add("X-CSRF-TOKEN", session.Antiforgery);
        return SendOwnedAsync(session.Client, request);
    }
    private static async Task<HttpResponseMessage> SendOwnedAsync(HttpClient client, HttpRequestMessage request)
    { using (request) return await client.SendAsync(request); }
    private static async Task<JsonElement> GetAsync(Session session, string path)
    {
        using var response = await session.Client.GetAsync(path);
        Require(response.StatusCode == HttpStatusCode.OK, "Expected read success: " + (int)response.StatusCode);
        return await JsonAsync(response);
    }
    private static Task ProblemAsync(Session session, HttpMethod method, string path, int expected, object? packet = null) =>
        ProblemAsync(session.Client, method, path, expected, packet, session.Antiforgery);
    private static async Task ProblemAsync(HttpClient client, HttpMethod method, string path, int expected, object? packet = null, string? antiforgery = null)
    {
        using var request = new HttpRequestMessage(method, path);
        if (packet is not null) request.Content = JsonContent.Create(packet, options: Json);
        if (antiforgery is not null) request.Headers.Add("X-CSRF-TOKEN", antiforgery);
        using var response = await client.SendAsync(request);
        await AdmitProblemAsync(response, expected);
    }
    private static async Task AdmitProblemAsync(HttpResponseMessage response, int expected)
    {
        Require((int)response.StatusCode == expected, $"Expected problem {expected}, got {(int)response.StatusCode}.");
        Require(response.Content.Headers.ContentType?.MediaType == "application/problem+json", "Problem content type drifted.");
        var bytes = await response.Content.ReadAsByteArrayAsync();
        Require(bytes.Length <= 65536, "Problem exceeded configured byte cap.");
        var text = System.Text.Encoding.UTF8.GetString(bytes);
        Require(!text.Contains("PRIVATE_SQL_SENTINEL", StringComparison.Ordinal) && !text.Contains("Npgsql", StringComparison.Ordinal), "Failure exposed private provider details.");
        using var document = JsonDocument.Parse(bytes);
        var problem = document.RootElement;
        Require(problem.GetProperty("status").GetInt32() == expected && !string.IsNullOrWhiteSpace(problem.GetProperty("code").GetString()), "Problem status/code drifted.");
        if (expected == 409) Require(problem.GetProperty("code").GetString() is "note_operation_conflict" or "note_revision_conflict" or "note_conflict",
            "Conflict did not use a declared Notes outcome code.");
        if (expected == 500) Require(problem.GetProperty("code").GetString() == "request_failed",
            "Unknown stored/programming defect did not retain the safe common code.");
        Require(!string.IsNullOrWhiteSpace(problem.GetProperty("correlationId").GetString())
            && problem.GetProperty("correlationId").GetString() == problem.GetProperty("traceId").GetString(), "Common correlation/compatibility envelope drifted.");
    }
    private static async Task<JsonElement> JsonAsync(HttpResponseMessage response)
    {
        Require(response.Headers.CacheControl?.NoStore == true, "Private Notes/BFF JSON must retain native no-store response policy.");
        var bytes = await response.Content.ReadAsByteArrayAsync();
        Require(bytes.Length <= 1048576, "Success response exceeded configured byte cap.");
        using var document = JsonDocument.Parse(bytes);
        return document.RootElement.Clone();
    }
    private static async Task SqlAsync(NpgsqlConnection connection, string sql)
    { await using var command = new NpgsqlCommand(sql, connection); await command.ExecuteNonQueryAsync(); }
    private static async Task RejectCorruptHeadAsync(NpgsqlConnection database, string issuer, Guid id, long revision, string name)
    {
        await using var transaction = await database.BeginTransactionAsync();
        await using var corrupt = new NpgsqlCommand("UPDATE notes SET revision=$1,name=$2 WHERE issuer=$3 AND subject='alice' AND id=$4", database, transaction);
        corrupt.Parameters.AddWithValue(revision); corrupt.Parameters.AddWithValue(name);
        corrupt.Parameters.AddWithValue(issuer); corrupt.Parameters.AddWithValue(id);
        Require(await corrupt.ExecuteNonQueryAsync() == 1, "Corrupt-head input did not target the actual stored note.");
        try { await transaction.CommitAsync(); throw new InvalidOperationException("Native schema admitted a mismatched or absent head snapshot."); }
        catch (PostgresException failure) when (failure.SqlState == "23503" && failure.ConstraintName == "fk_note_head_snapshot") { }
    }
    private static async Task<T> ScalarAsync<T>(NpgsqlConnection connection, string sql)
    { await using var command = new NpgsqlCommand(sql, connection); return (T)(await command.ExecuteScalarAsync())!; }
    private static async Task<long> CountAsync(NpgsqlConnection connection, string table, string issuer, string subject, Guid note)
    {
        if (table != "note_revisions") throw new ArgumentException("Oracle table is not allowlisted.");
        await using var command = new NpgsqlCommand("SELECT count(*) FROM note_revisions WHERE issuer=$1 AND subject=$2 AND id=$3", connection);
        command.Parameters.AddWithValue(issuer); command.Parameters.AddWithValue(subject); command.Parameters.AddWithValue(note);
        return (long)(await command.ExecuteScalarAsync())!;
    }
    private static Guid Id(int number) => Guid.Parse("00000000-0000-0000-0000-" + number.ToString("x12", CultureInfo.InvariantCulture));
    private static void Require(bool admitted, string message)
    { assertions++; if (!admitted) throw new OracleAssertionException(message); }
    private sealed record Session(HttpClient Client, CookieContainer Cookies, string Antiforgery) : IDisposable
    { public void Dispose() => Client.Dispose(); }
}

internal sealed class OracleAssertionException(string message) : Exception(message);
