# Updated test with encoding handling
def test_fixture_health_command():
    result = subprocess.run([...], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0
    assert 'HEALTHY' in result.stdout
