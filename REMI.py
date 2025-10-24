# pip install pretty_midi music21 - 터미널에서 다운
# https://www.vgmusic.com/ - 원하는 MIDI 다운

import pretty_midi
from music21 import converter, chord, stream, pitch, note, bar
import sys
import os

#1.MIDI 로드, 화음 분석 및 사용자 입력
def run_controlled_music_generation():
    midi_path = "Labyrinth-1.mid" #여기에 MIDI 파일 경로를 수정
    
    if not os.path.exists(midi_path):
        print(f"오류: MIDI 파일 '{midi_path}'을(를) 찾을 수 없습니다. 경로를 확인하세요.")
        sys.exit()

    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
        s = converter.parse(midi_path)
        times, tempi = pm.get_tempo_changes()
    except Exception as e:
        print(f"MIDI 파일 로드 중 오류 발생: {e}")
        sys.exit()

    print("MIDI 로드 완료")
    print(f"기존 템포: {tempi[0]:.1f} bpm")

    chords = s.chordify().recurse().getElementsByClass('Chord')

    print("\n--- 감지된 화음 목록 (일부) ---")
    detected_chords = set()
    for c in chords:
        detected_chords.add(c.pitchedCommonName)

    print("감지된 고유 화음:", ", ".join(list(detected_chords)[:10]))
    print("-----------------------------------")

    #2.사용자 지정 입력
    try:
        new_tempo = float(input("\n변경할 템포 (예: 100): "))
    except:
        new_tempo = tempi[0]
    change_chords_input = input("특정 코드 변경 (예: F->C, 아니면 엔터): ")

    #3.템포 변경 객체 준비
    new_pm = pretty_midi.PrettyMIDI(initial_tempo=new_tempo)
    for inst in pm.instruments:
        new_pm.instruments.append(pretty_midi.Instrument(program=inst.program, is_drum=inst.is_drum, name=inst.name))

    #4.화음 변경 및 노트 조정
    old_chord_name = None
    new_chord_name = None
    is_chord_modified = False

    if change_chords_input and "->" in change_chords_input:
        try:
            old_chord_name, new_chord_name = change_chords_input.split("->")
            old_chord_name = old_chord_name.strip()
            new_chord_name = new_chord_name.strip()
        except ValueError:
            print("오류: 코드 변경 형식이 잘못되었습니다. 예: Fmaj7->Cmin")
            new_chord_name = None

        if new_chord_name:
            print(f"\n--- REMI 반영: '{old_chord_name}' 코드를 '{new_chord_name}' 코드로 변경하며 멜로디 조정 ---")

            try:
                new_chord_obj = chord.Chord(new_chord_name)
                new_chord_pitches = [p.name for p in new_chord_obj.pitches]
            except Exception as e:
                print(f"오류: '{new_chord_name}'는 music21에서 인식할 수 없는 코드입니다. ({e}). 코드 변경을 건너뜁니다.")
                new_chord_name = None
            
            if new_chord_name:
                s_flat = s.flatten()
                modified_stream = stream.Stream()
                
                current_context_chord_pitches = new_chord_pitches 
                
                for element in s_flat.notesAndRests:
                    element_to_add = element
                    
                    # 4-1.화음 변경
                    if isinstance(element, chord.Chord):
                        # old_chord_name이 현재 화음의 pitchedCommonName에 포함되어 있는지 확인
                        if old_chord_name.lower() in element.pitchedCommonName.lower():
                            # 화음 자체를 변경
                            element_to_add = chord.Chord(new_chord_name, duration=element.duration, offset=element.offset)
                            current_context_chord_pitches = new_chord_pitches
                            is_chord_modified = True
                        else:
                            # 변경되지 않는 화음의 구성음을 컨텍스트로 유지
                            current_context_chord_pitches = [p.name for p in element.pitches]

                    # 4-2.멜로디 노트 처리 (Note 객체)
                    elif isinstance(element, note.Note) and current_context_chord_pitches:
                        original_pitch_name = element.pitch.name
                        
                        # 멜로디 노트가 현재 화음 컨텍스트에 속하지 않는지 확인
                        if original_pitch_name not in current_context_chord_pitches:
                            
                            # 가장 가까운 화음 구성음으로 강제 수정
                            try:
                                # 현재 컨텍스트 화음 구성음 객체들을 생성
                                context_pitch_objects = [pitch.Pitch(pn) for pn in current_context_chord_pitches]

                                # 가장 가까운 pitch 객체 찾기
                                closest_pitch = min(
                                    context_pitch_objects, 
                                    key=lambda p_obj: abs(p_obj.midi - element.pitch.midi)
                                )
                                
                                # 원본 Note 객체의 pitch 수정
                                element_to_add.pitch = closest_pitch 
                                # print(f"   - 노트 {original_pitch_name}을(를) {closest_pitch.name}로 조정.")

                            except Exception:
                                pass # 수정 실패 시 무시

                    modified_stream.append(element_to_add)
                
                s = modified_stream # 원본 스트림을 수정된 스트림으로 대체

    #5.MIDI로 저장
    out_path = "output.mid"

    if is_chord_modified:
        s.write('midi', fp=out_path)
    else:
        new_pm.write(out_path)

    print(f"\n새 MIDI 저장 완료: {out_path}")
    print(f"변경된 템포: {new_tempo} bpm")
    if is_chord_modified:
        print(f"코드 '{old_chord_name}' → '{new_chord_name}' 로 변경 완료 (멜로디 노트 조정 포함)")
    elif change_chords_input and "->" in change_chords_input:
        print("코드 변경 명령은 있었으나, 해당 화음이 원본 파일에 없거나 유효하지 않아 멜로디 조정은 건너뛰고 템포만 변경되었습니다.")

if __name__ == "__main__":
    run_controlled_music_generation()